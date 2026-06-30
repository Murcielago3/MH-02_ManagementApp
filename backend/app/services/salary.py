"""Point-in-time salary resolution and frozen timesheet costing.

The salary in effect on a date is the ``SalaryHistory`` row with the greatest
``effective_from <= date`` (earliest row floors any earlier date). Each row
already stores its own frozen ``hourly_rate``, so costing never depends on the
*current* salary or on live Settings.

Costing is frozen onto each timesheet entry at approval (``freeze_entry_cost``)
and rewritten by ``recompute_employee_costs`` whenever salary history changes
(including a backdated raise). Read paths just sum ``entry.employee_cost``.
"""
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.salary_history import SalaryHistory
from app.models.weekly_timesheet import WeeklyTimesheet, WeeklyTimesheetEntry


# ─────────────────────────── pure helpers ───────────────────────────

def compute_hourly_rate(monthly_salary, salary_hour, smpy, whpm) -> float:
    """Mirror of the legacy formula: explicit salary_hour wins, else
    (base * salary_months_per_year / 12) / working_hours_per_month."""
    if salary_hour and float(salary_hour) > 0:
        return round(float(salary_hour), 2)
    base = float(monthly_salary or 0)
    smpy = float(smpy or 13)
    whpm = float(whpm or 160)
    if base <= 0 or whpm <= 0:
        return 0.0
    return round((base * smpy / 12) / whpm, 2)


def _period_for_date(periods, d):
    """periods sorted by effective_from asc -> the row covering date d, or the
    earliest row as a floor for dates before any period. None if no periods."""
    chosen = None
    for p in periods:
        if p.effective_from <= d:
            chosen = p
        else:
            break
    if chosen is None and periods:
        chosen = periods[0]
    return chosen


def freeze_entry_cost(periods, daily_hours, hours, week_start):
    """Compute (total_cost, breakdown) for one entry by bucketing its days into
    salary periods. ``daily_hours`` (Mon..Sun, aligned to week_start) is the
    source of truth; legacy NULL falls back to even-spread of ``hours``.

    breakdown = [{salary_history_id, hours, rate, cost}, ...] — one bucket
    normally, two when the week straddles a raise. Returns plain floats/ints.
    """
    if isinstance(daily_hours, list) and len(daily_hours) > 0:
        days = [float(h or 0) for h in daily_hours]
    else:
        per = float(hours or 0) / 7.0          # legacy even-spread
        days = [per] * 7

    buckets = {}  # salary_history_id -> {hours, cost, rate}
    for i, h in enumerate(days):
        if h <= 0:
            continue
        d = week_start + timedelta(days=i)
        p = _period_for_date(periods, d)
        rate = float(p.hourly_rate or 0) if p else 0.0
        sh_id = p.id if p else None
        b = buckets.setdefault(sh_id, {"salary_history_id": sh_id, "hours": 0.0, "cost": 0.0, "rate": rate})
        b["hours"] += h
        b["cost"] += h * rate

    breakdown, total = [], 0.0
    for b in buckets.values():
        cost = round(b["cost"], 2)
        breakdown.append({
            "salary_history_id": b["salary_history_id"],
            "hours": round(b["hours"], 2),
            "rate": b["rate"],
            "cost": cost,
        })
        total += cost
    return round(total, 2), breakdown


# ─────────────────────────── db helpers ───────────────────────────

async def get_periods(db: AsyncSession, user_id: int):
    return (await db.execute(
        select(SalaryHistory)
        .where(SalaryHistory.user_id == user_id)
        .order_by(SalaryHistory.effective_from)
    )).scalars().all()


async def resolve_period(db: AsyncSession, user_id: int, on_date: date):
    return _period_for_date(await get_periods(db, user_id), on_date)


async def current_period(db: AsyncSession, user_id: int):
    return await resolve_period(db, user_id, date.today())


async def recompute_employee_costs(db: AsyncSession, user_id: int, from_date: date | None = None):
    """Re-freeze a user's approved timesheet entries from current salary history.

    ``from_date`` limits work to weeks ending on/after that date (used for
    backdated raises). Commits, then invalidates the reserve/dashboard caches.
    """
    periods = await get_periods(db, user_id)

    q = (
        select(WeeklyTimesheetEntry, WeeklyTimesheet.week_start)
        .join(WeeklyTimesheet, WeeklyTimesheet.id == WeeklyTimesheetEntry.timesheet_id)
        .where(WeeklyTimesheet.employee_id == user_id, WeeklyTimesheet.status == "approved")
    )
    if from_date is not None:
        q = q.where(WeeklyTimesheet.week_end >= from_date)

    for entry, week_start in (await db.execute(q)).all():
        total, breakdown = freeze_entry_cost(periods, entry.daily_hours, entry.hours, week_start)
        entry.employee_cost = total
        entry.cost_breakdown = breakdown

    await db.commit()

    try:
        from app.routers.projects import _invalidate_reserve
        _invalidate_reserve()
    except Exception:
        pass
