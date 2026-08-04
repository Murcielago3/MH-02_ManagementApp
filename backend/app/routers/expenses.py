from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pydantic import BaseModel
from app.database import get_db
from app.models.expense import Expense
from app.models.expense_party import ExpenseParty, ExpensePayment
from app.auth import require_admin, require_manager

router = APIRouter(prefix="/expenses", tags=["expenses"])


def _q(v) -> Decimal:
    return Decimal(str(v or 0))


def _round(v) -> Decimal:
    return _q(v).quantize(Decimal("0.01"), ROUND_HALF_UP)


# ── Parties ─────────────────────────────────────────────────────────────────
class PartyCreate(BaseModel):
    name: str
    gstin: Optional[str] = None
    pan: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    default_gst_percent: Optional[float] = 18
    notes: Optional[str] = None


class PartyUpdate(PartyCreate):
    name: Optional[str] = None


def _serialize_party(p) -> dict:
    return {
        "id": p.id, "name": p.name, "gstin": p.gstin, "pan": p.pan,
        "phone": p.phone, "email": p.email, "address": p.address,
        "default_gst_percent": float(p.default_gst_percent) if p.default_gst_percent is not None else None,
        "notes": p.notes,
    }


@router.get("/parties")
async def list_parties(db: AsyncSession = Depends(get_db), current_user=Depends(require_manager)):
    rows = (await db.execute(select(ExpenseParty).order_by(ExpenseParty.name))).scalars().all()
    return [_serialize_party(p) for p in rows]


@router.post("/parties", status_code=201)
async def create_party(data: PartyCreate, db: AsyncSession = Depends(get_db),
                       current_user=Depends(require_manager)):
    if not data.name or not data.name.strip():
        raise HTTPException(400, "Party name is required")
    p = ExpenseParty(**{**data.model_dump(), "name": data.name.strip(), "created_by": current_user.id})
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return _serialize_party(p)


@router.patch("/parties/{party_id}")
async def update_party(party_id: int, data: PartyUpdate, db: AsyncSession = Depends(get_db),
                       current_user=Depends(require_manager)):
    p = (await db.execute(select(ExpenseParty).where(ExpenseParty.id == party_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Party not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(p, k, v.strip() if k == "name" and v else v)
    await db.commit()
    await db.refresh(p)
    return _serialize_party(p)


@router.delete("/parties/{party_id}", status_code=204)
async def delete_party(party_id: int, db: AsyncSession = Depends(get_db),
                       current_user=Depends(require_admin)):
    p = (await db.execute(select(ExpenseParty).where(ExpenseParty.id == party_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Party not found")
    await db.delete(p)
    await db.commit()


# ── Expenses ────────────────────────────────────────────────────────────────
class ExpenseCreate(BaseModel):
    title: str
    category: str
    # base_amount + gst_percent are the source of truth; `amount` (total) is
    # derived. Legacy callers that only send `amount` still work.
    base_amount: Optional[float] = None
    gst_percent: Optional[float] = 0
    amount: Optional[float] = None
    party_id: Optional[int] = None
    date: date
    recurring: bool = False
    notes: Optional[str] = None


class ExpenseUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    base_amount: Optional[float] = None
    gst_percent: Optional[float] = None
    amount: Optional[float] = None
    party_id: Optional[int] = None
    date: Optional[date] = None
    recurring: Optional[bool] = None
    notes: Optional[str] = None


def _compute_amounts(base, gst_pct, fallback_total):
    """Return (base, gst_pct, gst_amount, total). If only a total was given
    (legacy), treat it as the base with no GST."""
    if base is None and fallback_total is not None:
        base = fallback_total
        gst_pct = 0
    base = _round(base)
    gst_pct = _q(gst_pct)
    gst_amount = _round(base * gst_pct / Decimal("100"))
    total = _round(base + gst_amount)
    return base, gst_pct, gst_amount, total


async def _settled_map(db, expense_ids):
    if not expense_ids:
        return {}
    rows = (await db.execute(
        select(ExpensePayment.expense_id, func.coalesce(func.sum(ExpensePayment.amount), 0))
        .where(ExpensePayment.expense_id.in_(expense_ids)).group_by(ExpensePayment.expense_id)
    )).all()
    return {eid: float(s) for eid, s in rows}


def _serialize_expense(e, settled: float, party_name=None) -> dict:
    total = float(e.amount or 0)
    settled = round(float(settled or 0), 2)
    remaining = round(total - settled, 2)
    status = "paid" if (total > 0 and settled >= total - 0.01) else ("partial" if settled > 0 else "unpaid")
    return {
        "id": e.id, "title": e.title, "category": e.category,
        "base_amount": float(e.base_amount) if e.base_amount is not None else None,
        "gst_percent": float(e.gst_percent) if e.gst_percent is not None else 0,
        "gst_amount": float(e.gst_amount) if e.gst_amount is not None else 0,
        "amount": total,
        "party_id": e.party_id, "party_name": party_name,
        "date": str(e.date) if e.date else None,
        "recurring": e.recurring, "notes": e.notes,
        "paid_amount": settled, "remaining_amount": max(remaining, 0.0),
        "payment_status": status,
    }


@router.get("/")
async def list_expenses(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager),
):
    query = select(Expense)
    if category:
        query = query.where(Expense.category == category)
    expenses = (await db.execute(query)).scalars().all()
    settled = await _settled_map(db, [e.id for e in expenses])
    party_ids = {e.party_id for e in expenses if e.party_id}
    names = {}
    if party_ids:
        names = dict((await db.execute(
            select(ExpenseParty.id, ExpenseParty.name).where(ExpenseParty.id.in_(party_ids))
        )).all())
    return [_serialize_expense(e, settled.get(e.id, 0.0), names.get(e.party_id)) for e in expenses]


@router.post("/", status_code=201)
async def create_expense(data: ExpenseCreate, db: AsyncSession = Depends(get_db),
                        current_user=Depends(require_manager)):
    base, gst_pct, gst_amount, total = _compute_amounts(data.base_amount, data.gst_percent, data.amount)
    expense = Expense(
        title=data.title, category=data.category,
        base_amount=base, gst_percent=gst_pct, gst_amount=gst_amount, amount=total,
        party_id=data.party_id, date=data.date, recurring=data.recurring,
        notes=data.notes, added_by=current_user.id,
    )
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return _serialize_expense(expense, 0.0)


@router.patch("/{expense_id}")
async def update_expense(expense_id: int, data: ExpenseUpdate, db: AsyncSession = Depends(get_db),
                        current_user=Depends(require_manager)):
    e = (await db.execute(select(Expense).where(Expense.id == expense_id))).scalar_one_or_none()
    if not e:
        raise HTTPException(404, "Expense not found")
    fields = data.model_dump(exclude_unset=True)
    for k in ("title", "category", "party_id", "date", "recurring", "notes"):
        if k in fields:
            setattr(e, k, fields[k])
    # Recompute money if any money field changed.
    if any(k in fields for k in ("base_amount", "gst_percent", "amount")):
        base = fields.get("base_amount", float(e.base_amount) if e.base_amount is not None else None)
        gst_pct = fields.get("gst_percent", float(e.gst_percent) if e.gst_percent is not None else 0)
        base, gst_pct, gst_amount, total = _compute_amounts(base, gst_pct, fields.get("amount"))
        e.base_amount, e.gst_percent, e.gst_amount, e.amount = base, gst_pct, gst_amount, total
    await db.commit()
    await db.refresh(e)
    settled = (await _settled_map(db, [e.id])).get(e.id, 0.0)
    return _serialize_expense(e, settled)


@router.delete("/{expense_id}", status_code=204)
async def delete_expense(expense_id: int, db: AsyncSession = Depends(get_db),
                        current_user=Depends(require_admin)):
    e = (await db.execute(select(Expense).where(Expense.id == expense_id))).scalar_one_or_none()
    if not e:
        raise HTTPException(404, "Expense not found")
    await db.delete(e)
    await db.commit()


# ── Expense payments (bills paid in parts) ──────────────────────────────────
class ExpensePaymentCreate(BaseModel):
    amount: float
    payment_date: date
    note: Optional[str] = None


def _serialize_expense_payment(p) -> dict:
    return {
        "id": p.id, "expense_id": p.expense_id, "amount": float(p.amount or 0),
        "payment_date": str(p.payment_date) if p.payment_date else None, "note": p.note,
    }


@router.get("/{expense_id}/payments")
async def list_expense_payments(expense_id: int, db: AsyncSession = Depends(get_db),
                               current_user=Depends(require_manager)):
    e = (await db.execute(select(Expense).where(Expense.id == expense_id))).scalar_one_or_none()
    if not e:
        raise HTTPException(404, "Expense not found")
    rows = (await db.execute(
        select(ExpensePayment).where(ExpensePayment.expense_id == expense_id)
        .order_by(ExpensePayment.payment_date, ExpensePayment.id)
    )).scalars().all()
    settled = sum(float(p.amount or 0) for p in rows)
    total = float(e.amount or 0)
    return {
        "expense_id": expense_id, "total": total,
        "paid_amount": round(settled, 2), "remaining_amount": round(max(total - settled, 0), 2),
        "payment_status": "paid" if (total > 0 and settled >= total - 0.01) else ("partial" if settled > 0 else "unpaid"),
        "payments": [_serialize_expense_payment(p) for p in rows],
    }


@router.post("/{expense_id}/payments", status_code=201)
async def add_expense_payment(expense_id: int, data: ExpensePaymentCreate,
                             db: AsyncSession = Depends(get_db), current_user=Depends(require_manager)):
    e = (await db.execute(select(Expense).where(Expense.id == expense_id))).scalar_one_or_none()
    if not e:
        raise HTTPException(404, "Expense not found")
    if _q(data.amount) <= 0:
        raise HTTPException(400, "Amount must be greater than 0")
    p = ExpensePayment(expense_id=expense_id, amount=_round(data.amount),
                       payment_date=data.payment_date, note=data.note, created_by=current_user.id)
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return _serialize_expense_payment(p)


@router.delete("/payments/{payment_id}", status_code=204)
async def delete_expense_payment(payment_id: int, db: AsyncSession = Depends(get_db),
                                current_user=Depends(require_manager)):
    p = (await db.execute(select(ExpensePayment).where(ExpensePayment.id == payment_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Payment not found")
    await db.delete(p)
    await db.commit()
