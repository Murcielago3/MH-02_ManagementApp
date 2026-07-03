"""Salary increments — admin-only, effective-dated.

Salary is *only* changed here (never via the user profile). Each increment adds
a SalaryHistory period, snapshots the hourly-rate inputs, re-derives the
effective_to bounds, refreshes the current-salary mirror on the user, re-freezes
affected timesheet costs, and (if backdated into last month) reopens that month's
salary slip for re-approval. See app/services/salary.py for the costing engine.
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.auth import require_admin
from app.models.user import User
from app.models.salary_history import SalaryHistory
from app.services.salary import (
    compute_hourly_rate, get_periods, current_period, recompute_employee_costs,
)
from app.routers.settings import get_settings_snapshot
from app.services.audit import log_audit

router = APIRouter(prefix="/salary", tags=["salary"])

COSTED_ROLES = ("employee", "project_manager")


class IncrementCreate(BaseModel):
    monthly_salary: float
    effective_from: date
    salary_hour: Optional[float] = None
    note: Optional[str] = None


class IncrementUpdate(BaseModel):
    monthly_salary: Optional[float] = None
    salary_hour: Optional[float] = None
    note: Optional[str] = None


def _month_start(d: date) -> date:
    return d.replace(day=1)


def _prev_month_start(today: date) -> date:
    return date(today.year - 1, 12, 1) if today.month == 1 else date(today.year, today.month - 1, 1)


def _ser(p: SalaryHistory) -> dict:
    f = lambda v: float(v) if v is not None else None
    return {
        "id": p.id,
        "monthly_salary": f(p.monthly_salary),
        "salary_hour": f(p.salary_hour),
        "hourly_rate": f(p.hourly_rate),
        "smpy": f(p.smpy),
        "whpm": f(p.whpm),
        "effective_from": str(p.effective_from),
        "effective_to": str(p.effective_to) if p.effective_to else None,
        "note": p.note,
    }


async def _rebuild_effective_to(db: AsyncSession, user_id: int):
    """Derive effective_to for every period: next.effective_from - 1 (last = open)."""
    periods = await get_periods(db, user_id)
    for i, p in enumerate(periods):
        p.effective_to = (periods[i + 1].effective_from - timedelta(days=1)) if i + 1 < len(periods) else None
    await db.flush()


async def _sync_mirror(db: AsyncSession, user: User):
    """Keep user.salary_month/salary_hour pointing at the period covering today."""
    p = await current_period(db, user.id)
    if p is not None:
        user.salary_month = p.monthly_salary
        user.salary_hour = p.salary_hour
    await db.flush()


@router.get("/employees")
async def list_salary_employees(db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)):
    users = (await db.execute(
        select(User).where(User.is_active == True, User.role.in_(COSTED_ROLES)).order_by(User.name)
    )).scalars().all()
    out = []
    for u in users:
        p = await current_period(db, u.id)
        out.append({
            "id": u.id,
            "name": u.name,
            "designation": u.designation,
            "role": u.role,
            "current_salary": float(p.monthly_salary) if p and p.monthly_salary is not None else None,
            "current_hourly_rate": float(p.hourly_rate) if p and p.hourly_rate is not None else None,
            "effective_from": str(p.effective_from) if p else None,
        })
    return out


@router.get("/{user_id}/history")
async def salary_history(user_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(require_admin)):
    return [_ser(p) for p in await get_periods(db, user_id)]


@router.post("/{user_id}/increment", status_code=201)
async def add_increment(
    user_id: int,
    data: IncrementCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    if user.role not in COSTED_ROLES:
        raise HTTPException(400, "Salary history only applies to employees and project managers")

    eff = data.effective_from
    today = date.today()
    if eff.day != 1:
        raise HTTPException(400, "Effective date must be the 1st of a month (no mid-month changes)")

    periods = await get_periods(db, user_id)
    if not periods:
        # Seeding the very first period — allow back to the joining month.
        min_allowed = _month_start(user.joining_date) if user.joining_date else eff
    else:
        min_allowed = _prev_month_start(today)
    if eff < min_allowed:
        raise HTTPException(400, "Backdating is only allowed up to the start of last month")
    if user.end_date and eff > user.end_date:
        raise HTTPException(400, "Effective date is after the employee's exit date")
    if any(p.effective_from == eff for p in periods):
        raise HTTPException(400, "A salary record already exists for that effective date")

    snap = await get_settings_snapshot(db)
    smpy, whpm = snap["salary_months_per_year"], snap["working_hours_per_month"]
    rate = compute_hourly_rate(data.monthly_salary, data.salary_hour, smpy, whpm)

    db.add(SalaryHistory(
        user_id=user_id, monthly_salary=data.monthly_salary, salary_hour=data.salary_hour,
        smpy=smpy, whpm=whpm, hourly_rate=rate, effective_from=eff, note=data.note,
    ))
    await db.flush()
    await _rebuild_effective_to(db, user_id)
    await _sync_mirror(db, user)
    await log_audit(db, current_user, "salary.increment", "user", user_id,
                    summary=f"Salary increment for {user.name} to ₹{data.monthly_salary:,.0f} effective {eff}")
    await db.commit()

    # Re-freeze approved timesheet costs from the earliest affected date.
    await recompute_employee_costs(db, user_id, from_date=eff)

    # Backdated into a prior month -> reopen that month's slip for re-approval.
    if eff < _month_start(today):
        from app.routers.salary_slips import reopen_month_slip
        await reopen_month_slip(db, user_id, f"{eff.year:04d}-{eff.month:02d}")

    return [_ser(p) for p in await get_periods(db, user_id)]


@router.patch("/period/{period_id}")
async def edit_period(
    period_id: int,
    data: IncrementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Fix a wrong amount/note on an existing period; re-freezes from its date."""
    p = (await db.execute(select(SalaryHistory).where(SalaryHistory.id == period_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Salary record not found")

    snap = await get_settings_snapshot(db)
    if data.monthly_salary is not None:
        p.monthly_salary = data.monthly_salary
    if data.salary_hour is not None:
        p.salary_hour = data.salary_hour
    if data.note is not None:
        p.note = data.note
    p.hourly_rate = compute_hourly_rate(
        p.monthly_salary, p.salary_hour,
        p.smpy if p.smpy is not None else snap["salary_months_per_year"],
        p.whpm if p.whpm is not None else snap["working_hours_per_month"],
    )
    user = (await db.execute(select(User).where(User.id == p.user_id))).scalar_one_or_none()
    await _sync_mirror(db, user)
    await db.commit()
    await recompute_employee_costs(db, p.user_id, from_date=p.effective_from)
    return [_ser(x) for x in await get_periods(db, p.user_id)]


@router.delete("/period/{period_id}", status_code=200)
async def delete_period(
    period_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    p = (await db.execute(select(SalaryHistory).where(SalaryHistory.id == period_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Salary record not found")
    user_id, from_date = p.user_id, p.effective_from
    await db.delete(p)
    await db.flush()
    await _rebuild_effective_to(db, user_id)
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user:
        await _sync_mirror(db, user)
    await db.commit()
    await recompute_employee_costs(db, user_id, from_date=from_date)
    return [_ser(x) for x in await get_periods(db, user_id)]
