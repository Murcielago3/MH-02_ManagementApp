"""Quarterly task / subtask delivery report.

Quarters follow the Indian financial year: Q1 Apr–Jun, Q2 Jul–Sep, Q3 Oct–Dec,
Q4 Jan–Mar. ``fy_year`` names the year the FY opens in, so fy_year=2026 is
FY 2026-27 and its Q4 lands in Jan–Mar 2027.

An item belongs to the quarter its DEADLINE falls in — that's what "how many
went due this quarter" means. Buckets are mutually exclusive and sum to total:

    completed_on_time   finished on or before the deadline
    completed_late      finished, but after the deadline
    completed_untimed   finished before this feature shipped (no timestamp) —
                        reported honestly rather than assumed on-time
    overdue             not finished, deadline has passed
    open                not finished, deadline still ahead

``never_started`` counts items still sitting at 'pending' with no start stamp.
It overlaps the buckets above (an unstarted item is also overdue or open), so
it is reported separately and NOT summed into the total.
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_manager
from app.database import get_db
from app.models import Task, User
from app.models.project_stage import StageSubtask

router = APIRouter(prefix="/reports", tags=["reports"])

# FY quarter -> (start month, number of months in from FY start)
_Q_START_MONTH = {1: 4, 2: 7, 3: 10, 4: 1}


def quarter_range(fy_year: int, quarter: int):
    """(start, end) inclusive for an Indian-FY quarter. Q4 rolls into the
    following calendar year."""
    if quarter not in (1, 2, 3, 4):
        raise HTTPException(400, "quarter must be 1-4")
    month = _Q_START_MONTH[quarter]
    year = fy_year + 1 if quarter == 4 else fy_year
    start = date(year, month, 1)
    end_month, end_year = month + 2, year
    if end_month > 12:
        end_month -= 12
        end_year += 1
    nxt = date(end_year + (1 if end_month == 12 else 0),
               1 if end_month == 12 else end_month + 1, 1)
    return start, nxt - timedelta(days=1)


def current_fy_quarter(today: Optional[date] = None):
    today = today or date.today()
    m = today.month
    if m >= 4:
        return today.year, (m - 4) // 3 + 1
    return today.year - 1, 4          # Jan-Mar is Q4 of the FY that opened last April


def _blank():
    return {
        "total": 0,
        "completed_on_time": 0,
        "completed_late": 0,
        "completed_untimed": 0,
        "overdue": 0,
        "open": 0,
        "never_started": 0,
    }


def _classify(bucket, deadline, status, completed_at, started_at, today):
    """Fold one item into a bucket dict. ``deadline`` is a date, ``completed_at``
    a datetime or None."""
    bucket["total"] += 1
    if status == "completed":
        if completed_at is None:
            bucket["completed_untimed"] += 1
        elif completed_at.date() <= deadline:
            bucket["completed_on_time"] += 1
        else:
            bucket["completed_late"] += 1
    else:
        if deadline < today:
            bucket["overdue"] += 1
        else:
            bucket["open"] += 1
        if status == "pending" and started_at is None:
            bucket["never_started"] += 1


def _with_rates(b):
    """Attach the two percentages the report is actually read for."""
    finished = b["completed_on_time"] + b["completed_late"]
    b["completed"] = finished + b["completed_untimed"]
    b["on_time_rate"] = round(b["completed_on_time"] / finished * 100, 1) if finished else None
    b["completion_rate"] = round(b["completed"] / b["total"] * 100, 1) if b["total"] else None
    return b


@router.get("/quarterly")
async def quarterly_report(
    fy_year: Optional[int] = None,
    quarter: Optional[int] = Query(None, ge=1, le=4),
    employee_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    """Task + subtask delivery stats for one FY quarter. Pass employee_id to
    scope to one person; omit it for the studio-wide roll-up, which also
    returns a per-employee breakdown."""
    if fy_year is None or quarter is None:
        fy_year, quarter = current_fy_quarter()
    start, end = quarter_range(fy_year, quarter)
    today = date.today()

    # ── Subtasks: deadline is due_date; owner is the parent task's assignee ──
    sub_rows = (await db.execute(
        select(StageSubtask.due_date, StageSubtask.status, StageSubtask.completed_at,
               StageSubtask.started_at, Task.assigned_to)
        # Owner is whoever the stage's task band is assigned to; stage subtasks
        # with no task band report against no employee and are org-level only.
        .outerjoin(Task, Task.stage_id == StageSubtask.stage_id)
        .where(StageSubtask.due_date.isnot(None),
               StageSubtask.due_date >= start, StageSubtask.due_date <= end)
    )).all()

    # ── Tasks: deadline is end_date, falling back to the single-day date ──
    task_rows = (await db.execute(
        select(Task.date, Task.end_date, Task.status, Task.completed_at,
               Task.started_at, Task.assigned_to)
    )).all()

    subtasks, tasks = _blank(), _blank()
    per_emp = {}

    def emp_bucket(uid):
        return per_emp.setdefault(uid, {"tasks": _blank(), "subtasks": _blank()})

    for due, status, completed_at, started_at, owner in sub_rows:
        if employee_id and owner != employee_id:
            continue
        _classify(subtasks, due, status, completed_at, started_at, today)
        if not employee_id:
            _classify(emp_bucket(owner)["subtasks"], due, status, completed_at, started_at, today)

    for d, end_d, status, completed_at, started_at, owner in task_rows:
        deadline = end_d or d
        if deadline is None or not (start <= deadline <= end):
            continue
        if employee_id and owner != employee_id:
            continue
        _classify(tasks, deadline, status, completed_at, started_at, today)
        if not employee_id:
            _classify(emp_bucket(owner)["tasks"], deadline, status, completed_at, started_at, today)

    breakdown = []
    if not employee_id and per_emp:
        names = {u.id: u.name for u in (await db.execute(
            select(User).where(User.id.in_(list(per_emp.keys())))
        )).scalars().all()}
        breakdown = sorted(
            ({"employee_id": uid, "name": names.get(uid, f"#{uid}"),
              "tasks": _with_rates(v["tasks"]), "subtasks": _with_rates(v["subtasks"])}
             for uid, v in per_emp.items()),
            key=lambda r: -r["subtasks"]["total"],
        )

    return {
        "fy_year": fy_year,
        "quarter": quarter,
        "label": f"Q{quarter} FY{fy_year}-{str(fy_year + 1)[-2:]}",
        "range": {"start": str(start), "end": str(end)},
        "scope": "employee" if employee_id else "org",
        "employee_id": employee_id,
        "tasks": _with_rates(tasks),
        "subtasks": _with_rates(subtasks),
        "by_employee": breakdown,
    }


@router.get("/quarterly/available")
async def available_quarters(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    """Quarters that actually contain data, newest first — drives the picker so
    it never offers an empty quarter."""
    bounds = (await db.execute(select(StageSubtask.due_date).where(StageSubtask.due_date.isnot(None)))).scalars().all()
    task_ends = (await db.execute(select(Task.end_date))).scalars().all()
    task_starts = (await db.execute(select(Task.date))).scalars().all()
    all_dates = [d for d in list(bounds) + list(task_ends) + list(task_starts) if d]

    cur_fy, cur_q = current_fy_quarter()
    seen = {(cur_fy, cur_q)}
    for d in all_dates:
        fy, q = current_fy_quarter(d)
        seen.add((fy, q))

    return [
        {"fy_year": fy, "quarter": q, "label": f"Q{q} FY{fy}-{str(fy + 1)[-2:]}",
         "is_current": (fy, q) == (cur_fy, cur_q)}
        for fy, q in sorted(seen, reverse=True)
    ]
