from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.client import Client
from app.auth import require_admin, require_manager

router = APIRouter(prefix="/clients", tags=["clients"])

class ClientCreate(BaseModel):
    name: str
    email: str
    phone: str
    address: str

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

@router.get("/")
async def list_clients(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
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
    data:ClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    client = Client(
        name=data.name,
        email=data.email,
        phone=data.phone,
        address=data.address
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
    for field, value in data.model_dump(exclude_unset=True).items():
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