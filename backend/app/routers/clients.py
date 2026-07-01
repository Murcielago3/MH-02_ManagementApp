from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.client import Client
from app.auth import require_admin, require_manager
from app.utils.tax_ids import validate_pan, validate_gstin, pan_from_gstin

router = APIRouter(prefix="/clients", tags=["clients"])

CUSTOMER_TYPES = ("business", "individual")


class ClientCreate(BaseModel):
    name: str
    email: str
    phone: str
    address: Optional[str] = None
    gstin: Optional[str] = None
    customer_type: str = "business"
    pan: Optional[str] = None
    salutation: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    gstin: Optional[str] = None
    customer_type: Optional[str] = None
    pan: Optional[str] = None
    salutation: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None


def _compose_address(line1, line2, city, state, pincode) -> Optional[str]:
    """Fold structured address fields into the legacy single-string `address`
    column, so existing consumers (e.g. invoice bill_to_address auto-fill)
    keep working without change."""
    lines = [l for l in (line1, line2) if l]
    city_state_pin = ", ".join(p for p in (city, state) if p)
    if pincode:
        city_state_pin = f"{city_state_pin} - {pincode}" if city_state_pin else pincode
    if city_state_pin:
        lines.append(city_state_pin)
    return "\n".join(lines) if lines else None


def _normalize_and_validate(data: dict, existing: Optional[Client] = None) -> dict:
    """Uppercase + validate GSTIN/PAN, enforce customer_type rules, autofill PAN
    from GSTIN, and (re)compose the legacy `address` string. Mutates and
    returns `data` (a dict of fields about to be applied to the ORM row)."""
    customer_type = data.get("customer_type") or (existing.customer_type if existing else "business")
    if customer_type not in CUSTOMER_TYPES:
        raise HTTPException(400, f"customer_type must be one of {CUSTOMER_TYPES}")
    data["customer_type"] = customer_type

    if "gstin" in data and data["gstin"]:
        data["gstin"] = data["gstin"].strip().upper()
    if "pan" in data and data["pan"]:
        data["pan"] = data["pan"].strip().upper()

    if customer_type == "individual":
        # Individuals never carry a GSTIN, regardless of what was sent.
        data["gstin"] = None
        pan = data.get("pan") if "pan" in data else (existing.pan if existing else None)
        if not pan:
            raise HTTPException(400, "PAN is required for individual clients")
        err = validate_pan(pan)
        if err:
            raise HTTPException(400, err)
    else:
        gstin = data.get("gstin") if "gstin" in data else (existing.gstin if existing else None)
        if gstin:
            err = validate_gstin(gstin)
            if err:
                raise HTTPException(400, err)
            # Auto-derive PAN from GSTIN if no PAN is set (new or existing).
            current_pan = data.get("pan") if "pan" in data else (existing.pan if existing else None)
            if not current_pan:
                data["pan"] = pan_from_gstin(gstin)
        pan = data.get("pan") if "pan" in data else (existing.pan if existing else None)
        if pan:
            err = validate_pan(pan)
            if err:
                raise HTTPException(400, err)

    # Recompose the legacy `address` string whenever any structured field changes.
    if any(k in data for k in ("address_line1", "address_line2", "city", "state", "pincode")):
        line1 = data.get("address_line1", existing.address_line1 if existing else None)
        line2 = data.get("address_line2", existing.address_line2 if existing else None)
        city = data.get("city", existing.city if existing else None)
        state = data.get("state", existing.state if existing else None)
        pincode = data.get("pincode", existing.pincode if existing else None)
        composed = _compose_address(line1, line2, city, state, pincode)
        if composed:
            data["address"] = composed

    return data


@router.get("/")
async def list_clients(
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    # Clients change rarely; browser can cache for 30s.
    response.headers["Cache-Control"] = "private, max-age=30"
    result = await db.execute(select(Client))
    clients = result.scalars().all()
    return clients

@router.get("/{client_id}")
async def get_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.post("/", status_code=201)
async def create_client(
    data: ClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    payload = _normalize_and_validate(data.model_dump())
    client = Client(
        name=payload["name"],
        email=payload["email"],
        phone=payload["phone"],
        address=payload.get("address") or "",
        gstin=payload.get("gstin"),
        customer_type=payload["customer_type"],
        pan=payload.get("pan"),
        salutation=payload.get("salutation"),
        address_line1=payload.get("address_line1"),
        address_line2=payload.get("address_line2"),
        city=payload.get("city"),
        state=payload.get("state"),
        pincode=payload.get("pincode"),
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client

@router.patch("/{client_id}")
async def update_client(
    client_id: int,
    data: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(404, "Client not found")
    update_data = _normalize_and_validate(data.model_dump(exclude_unset=True), existing=client)
    for field, value in update_data.items():
        setattr(client, field, value)
    await db.commit()
    await db.refresh(client)
    return client

@router.delete("/{client_id}")
async def delete_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(404, "Client not found")
    await db.delete(client)
    await db.commit()
