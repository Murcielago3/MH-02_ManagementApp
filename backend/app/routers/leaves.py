from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import date, timedelta
from calendar import monthrange
from decimal import Decimal
from pydantic import BaseModel
from app.database import get_db
from app.models.leave import LeaveRequest
from app.models.user import User
from app.auth import get_current_user, require_admin, require_manager

router = APIRouter(prefix="/leaves", tags=["leaves"])

MONTHLY_ACCRUAL = Decimal("1.5")
PROBATION_MONTHS = 3


# ─── Date helpers ─────────────────────────────────────────────────────────────
def working_days(start: date, end: date) -> list[date]:
    """All Mon–Fri dates in [start, end] inclusive."""
    if not start or not end or end < start:
        return []
    out = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def add_months_date(d: date, months: int) -> date:
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    day = min(d.day, monthrange(y, m)[1])
    return date(y, m, day)


def probation_end(joining: date) -> Optional[date]:
    return add_months_date(joining, PROBATION_MONTHS) if joining else None


def _month_str(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _months_between(from_ms: str, to_ms: str) -> int:
    fy, fm = (int(x) for x in from_ms.split("-"))
    ty, tm = (int(x) for x in to_ms.split("-"))
    return (ty * 12 + tm) - (fy * 12 + fm)


# ─── Monthly accrual (idempotent, no scheduler) ──────────────────────────────
async def accrue_all(db: AsyncSession) -> int:
    """Credit 1.5 paid-leave days for every elapsed month, once each.

    First time an employee is seen, seed a single credit for the current month.
    Returns number of users whose balance changed.
    """
    today = date.today()
    cur = _month_str(today)
    res = await db.execute(select(User).where(User.is_active == True))  # noqa: E712
    users = res.scalars().all()
    changed = 0
    for u in users:
        bal = Decimal(str(u.paid_leave_balance or 0))
        if u.leave_accrued_through is None:
            u.paid_leave_balance = bal + MONTHLY_ACCRUAL
            u.leave_accrued_through = cur
            changed += 1
        else:
            steps = _months_between(u.leave_accrued_through, cur)
            if steps > 0:
                u.paid_leave_balance = bal + MONTHLY_ACCRUAL * steps
                u.leave_accrued_through = cur
                changed += 1
    if changed:
        await db.commit()
    return changed


def classify_leave(leave: LeaveRequest, user: User):
    """Split a leave's working days into paid/unpaid against the user's balance
    and probation window. Returns (paid_days, unpaid_days, new_balance)."""
    bal = Decimal(str(user.paid_leave_balance or 0))
    pend = probation_end(user.joining_date)
    paid = 0
    unpaid = 0
    for d in working_days(leave.start_date, leave.end_date):
        if pend and d < pend:
            unpaid += 1
        elif bal >= 1:
            paid += 1
            bal -= 1
        else:
            unpaid += 1
    return paid, unpaid, bal


# ─── Schemas ──────────────────────────────────────────────────────────────────
class LeaveCreate(BaseModel):
    start_date: date
    end_date: date
    reason: str


class LeaveAction(BaseModel):
    status: str


# ─── Routes ───────────────────────────────────────────────────────────────────
@router.get("/")
async def list_leaves(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_manager),
):
    await accrue_all(db)
    result = await db.execute(select(LeaveRequest).options(selectinload(LeaveRequest.employee)))
    return result.scalars().all()


@router.get("/my")
async def my_leaves(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    await accrue_all(db)
    result = await db.execute(
        select(LeaveRequest).where(LeaveRequest.employee_id == current_user.id)
    )
    return result.scalars().all()


@router.post("/", status_code=201)
async def apply_leave(
    data: LeaveCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Leaves are never blocked — any days beyond the paid balance (or taken
    # during probation) simply become unpaid and are deducted from salary.
    wd = len(working_days(data.start_date, data.end_date))
    leave = LeaveRequest(
        employee_id=current_user.id,
        start_date=data.start_date,
        end_date=data.end_date,
        reason=data.reason,
        days_count=wd,
    )
    db.add(leave)
    await db.commit()
    await db.refresh(leave)
    return leave


@router.patch("/{leave_id}/action")
async def action_leave(
    leave_id: int,
    data: LeaveAction,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if data.status not in ["approved", "rejected"]:
        raise HTTPException(400, "Status must be approved or rejected")

    result = await db.execute(
        select(LeaveRequest)
        .where(LeaveRequest.id == leave_id)
        .options(selectinload(LeaveRequest.employee))
    )
    leave = result.scalar_one_or_none()
    if not leave:
        raise HTTPException(404, "Leave request not found")

    emp = leave.employee
    was_approved = leave.status == "approved"

    if data.status == "approved" and not was_approved:
        paid, unpaid, new_bal = classify_leave(leave, emp)
        leave.paid_days = paid
        leave.unpaid_days = unpaid
        emp.paid_leave_balance = new_bal
    elif data.status == "rejected" and was_approved:
        # Restore consumed paid days back to the balance
        emp.paid_leave_balance = Decimal(str(emp.paid_leave_balance or 0)) + Decimal(str(leave.paid_days or 0))
        leave.paid_days = 0
        leave.unpaid_days = 0

    leave.status = data.status
    await db.commit()
    await db.refresh(leave)
    return leave
