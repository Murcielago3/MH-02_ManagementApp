from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import date, timedelta
from pydantic import BaseModel
from app.database import get_db
from app.models.weekly_timesheet import WeeklyTimesheet, WeeklyTimesheetEntry
from app.models.user import User
from app.auth import get_current_user, require_admin, require_manager
from app.services.slack import notify_event

router = APIRouter(prefix="/weekly-timesheets", tags=["weekly-timesheets"])

class TimesheetEntryCreate(BaseModel):
    project_id: Optional[int] = None
    hours: float
    description: str
    daily_hours: Optional[List[float]] = None

class WeeklyTimesheetCreate(BaseModel):
    week_start: date
    week_end: date
    description: Optional[str] = None
    entries: List[TimesheetEntryCreate]

class TimesheetAction(BaseModel):
    status: str  # approved or rejected
    rejection_reason: Optional[str] = None

@router.get("/")
async def list_timesheets(
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    query = select(WeeklyTimesheet).options(selectinload(WeeklyTimesheet.entries))
    if employee_id:
        query = query.where(WeeklyTimesheet.employee_id == employee_id)
    if status:
        query = query.where(WeeklyTimesheet.status == status)
    
    result = await db.execute(query)
    timesheets = result.scalars().all()
    return timesheets

@router.get("/my")
async def my_timesheets(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    result = await db.execute(
        select(WeeklyTimesheet)
        .options(selectinload(WeeklyTimesheet.entries))
        .where(WeeklyTimesheet.employee_id == current_user.id)
        .order_by(WeeklyTimesheet.week_start.desc())
    )
    return result.scalars().all()

@router.get("/pending-weeks")
async def get_pending_weeks(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Returns all weeks that fall within the current calendar month
    today = date.today()
    weeks = []

    # First day of current month, and Monday of that week
    month_start = date(today.year, today.month, 1)
    first_monday = month_start - timedelta(days=month_start.weekday())

    # Monday of the current week (latest week to show)
    current_monday = today - timedelta(days=today.weekday())

    week_start = first_monday
    while week_start <= current_monday:
        week_end = week_start + timedelta(days=6)

        # Skip weeks entirely before the employee's joining date
        if week_end < current_user.joining_date:
            week_start += timedelta(weeks=1)
            continue

        # Check if a timesheet already exists for this week
        result = await db.execute(
            select(WeeklyTimesheet).where(
                WeeklyTimesheet.employee_id == current_user.id,
                WeeklyTimesheet.week_start == week_start
            )
        )
        existing = result.scalar_one_or_none()

        if not existing:
            weeks.append({
                "week_start": str(week_start),
                "week_end": str(week_end),
                "status": "pending"
            })
        else:
            weeks.append({
                "week_start": str(week_start),
                "week_end": str(week_end),
                "status": existing.status,
                "timesheet_id": existing.id
            })

        week_start += timedelta(weeks=1)

    return weeks

@router.post("/", status_code=201)
async def submit_timesheet(
    background_tasks: BackgroundTasks,
    data: WeeklyTimesheetCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Check not already submitted for this week
    existing = await db.execute(
        select(WeeklyTimesheet).where(
            WeeklyTimesheet.employee_id == current_user.id,
            WeeklyTimesheet.week_start == data.week_start
        )
    )
    existing_entry = existing.scalar_one_or_none()
    
    if existing_entry and existing_entry.status != "rejected":
        raise HTTPException(400, "Timesheet already submitted for this week")

    # If rejected, delete old entry and resubmit
    if existing_entry and existing_entry.status == "rejected":
        await db.delete(existing_entry)
        await db.flush()

    # daily_hours (Mon..Sun) is the single source of truth; hours is its sum.
    for e in data.entries:
        if not e.daily_hours or len(e.daily_hours) != 7:
            raise HTTPException(400, "Each entry must include daily_hours for all 7 days (Mon..Sun)")

    def _entry_hours(e):
        return round(sum(float(h or 0) for h in e.daily_hours), 2)

    total_hours = round(sum(_entry_hours(e) for e in data.entries), 2)

    timesheet = WeeklyTimesheet(
        employee_id=current_user.id,
        week_start=data.week_start,
        week_end=data.week_end,
        description=data.description,
        total_hours=total_hours,
        status="submitted"
    )
    db.add(timesheet)
    await db.flush()

    # Add detailed entries
    for entry_data in data.entries:
        entry = WeeklyTimesheetEntry(
            timesheet_id=timesheet.id,
            project_id=entry_data.project_id,
            hours=_entry_hours(entry_data),
            description=entry_data.description,
            daily_hours=entry_data.daily_hours
        )
        db.add(entry)

    await db.commit()
    await db.refresh(timesheet)

    # Notify the team channel in Slack (fires after the response; never blocks it).
    background_tasks.add_task(
        notify_event,
        "timesheet_uploaded",
        f"📋 *{current_user.name}* submitted a timesheet for the week of "
        f"{data.week_start} — {total_hours}h",
    )
    return timesheet

@router.get("/{timesheet_id}")
async def get_timesheet(
    timesheet_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    result = await db.execute(
        select(WeeklyTimesheet)
        .options(selectinload(WeeklyTimesheet.entries))
        .where(WeeklyTimesheet.id == timesheet_id)
    )
    timesheet = result.scalar_one_or_none()
    if not timesheet:
        raise HTTPException(404, "Timesheet not found")
    if current_user.role == "employee" and timesheet.employee_id != current_user.id:
        raise HTTPException(403, "Not your timesheet")
    return timesheet

@router.patch("/{timesheet_id}/action")
async def action_timesheet(
    timesheet_id: int,
    data: TimesheetAction,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    if data.status not in ["approved", "rejected"]:
        raise HTTPException(400, "Status must be approved or rejected")

    result = await db.execute(
        select(WeeklyTimesheet).where(WeeklyTimesheet.id == timesheet_id)
    )
    timesheet = result.scalar_one_or_none()
    if not timesheet:
        raise HTTPException(404, "Timesheet not found")

    timesheet.status = data.status
    if data.status == "rejected":
        timesheet.rejection_reason = data.rejection_reason

    # Freeze each entry's employee cost from the salary period(s) covering its
    # days, so historical project cost is immutable against later raises.
    if data.status == "approved":
        from app.services.salary import get_periods, freeze_entry_cost
        periods = await get_periods(db, timesheet.employee_id)
        entries = (await db.execute(
            select(WeeklyTimesheetEntry).where(WeeklyTimesheetEntry.timesheet_id == timesheet.id)
        )).scalars().all()
        for e in entries:
            total, breakdown = freeze_entry_cost(periods, e.daily_hours, e.hours, timesheet.week_start)
            e.employee_cost = total
            e.cost_breakdown = breakdown

    await db.commit()
    await db.refresh(timesheet)

    # Notify the team channel in Slack of the decision (the employee sees it here).
    emp_name = (await db.execute(
        select(User.name).where(User.id == timesheet.employee_id)
    )).scalar_one_or_none() or f"Employee #{timesheet.employee_id}"
    verb = "approved ✅" if data.status == "approved" else "rejected ❌"
    msg = f"🗂️ Timesheet *{verb}* — *{emp_name}*, week of {timesheet.week_start}"
    if data.status == "rejected" and timesheet.rejection_reason:
        msg += f"\nReason: _{timesheet.rejection_reason}_"
    background_tasks.add_task(notify_event, "timesheet_decision", msg)

    # An approval/rejection changes which hours count toward employee cost,
    # which affects the reserve balance shown in the sidebar.
    from app.routers.projects import _invalidate_reserve
    _invalidate_reserve()
    return timesheet