from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import date, timedelta, datetime, timezone
from pydantic import BaseModel
from app.database import get_db
from app.models.weekly_timesheet import WeeklyTimesheet, WeeklyTimesheetEntry
from app.models.user import User
from app.auth import get_current_user, require_admin, require_manager
from app.services.slack import notify_event, lookup_user_id
from app.services.audit import log_audit

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

class RejectBody(BaseModel):
    rejection_reason: Optional[str] = None

@router.get("/")
async def list_timesheets(
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    query = select(WeeklyTimesheet).options(selectinload(WeeklyTimesheet.entries))
    # Project managers must not see admin-submitted timesheets.
    if current_user.role == "project_manager":
        query = query.where(
            WeeklyTimesheet.employee_id.notin_(select(User.id).where(User.role == "admin"))
        )
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
        status="submitted",
        submitted_at=datetime.now(timezone.utc),
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

    await log_audit(db, current_user, "timesheet.submitted", "timesheet", timesheet.id,
                    summary=f"Submitted timesheet for week of {data.week_start} ({total_hours}h)")
    await db.commit()
    await db.refresh(timesheet)

    # Notify the team channel in Slack (fires after the response; never blocks it).
    # Tag the submitter so Slack emails them the confirmation.
    def _notify_timesheet_uploaded(user, week_start, total_hours):
        tag = f"<@{uid}>" if (uid := lookup_user_id(user.studio_email) or lookup_user_id(user.personal_mail)) else f"*{user.name}*"
        notify_event(
            "timesheet_uploaded",
            f"📋 {tag} submitted a timesheet for the week of "
            f"{week_start} — {total_hours}h",
        )
    background_tasks.add_task(_notify_timesheet_uploaded, current_user, data.week_start, total_hours)
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

def _recompute_status(ts, submitter_is_admin: bool):
    """Derive the stored `status` from the approval / rejection slots.

    Admin submitter → 'approved' once the single admin slot is filled (no PM,
        no second admin).
    Non-admin submitter → 'approved' only when the PM slot AND both admin slots
        are filled (two distinct admins).
    """
    if ts.rejected_at:
        ts.status = "rejected"
    elif submitter_is_admin:
        ts.status = "approved" if ts.admin_approved_at else "submitted"
    elif ts.pm_approved_at and ts.admin_approved_at and ts.admin2_approved_at:
        ts.status = "approved"
    elif ts.admin_approved_at:
        ts.status = "admin_approved"
    elif ts.pm_approved_at:
        ts.status = "pm_approved"
    else:
        ts.status = "submitted"


async def _freeze_entries(db, timesheet):
    """Freeze each entry's employee cost from the salary period(s) covering its
    days, so historical project cost is immutable against later raises."""
    from app.services.salary import get_periods, freeze_entry_cost
    periods = await get_periods(db, timesheet.employee_id)
    entries = (await db.execute(
        select(WeeklyTimesheetEntry).where(WeeklyTimesheetEntry.timesheet_id == timesheet.id)
    )).scalars().all()
    for e in entries:
        total, breakdown = freeze_entry_cost(periods, e.daily_hours, e.hours, timesheet.week_start)
        e.employee_cost = total
        e.cost_breakdown = breakdown


def _queue_decision_slack(background_tasks, emp, timesheet, status, rejection_reason):
    def _run(emp, timesheet, status, rejection_reason):
        if emp:
            uid = lookup_user_id(emp.studio_email) or lookup_user_id(emp.personal_mail)
            tag = f"<@{uid}>" if uid else f"*{emp.name}*"
        else:
            tag = f"*Employee #{timesheet.employee_id}*"
        verb = "approved ✅" if status == "approved" else "rejected ❌"
        msg = f"🗂️ Timesheet *{verb}* — {tag}, week of {timesheet.week_start}"
        if status == "rejected" and rejection_reason:
            msg += f"\nReason: _{rejection_reason}_"
        notify_event("timesheet_decision", msg)
    background_tasks.add_task(_run, emp, timesheet, status, rejection_reason)


async def _load_ts_and_submitter(db, timesheet_id):
    timesheet = (await db.execute(
        select(WeeklyTimesheet).where(WeeklyTimesheet.id == timesheet_id)
    )).scalar_one_or_none()
    if not timesheet:
        raise HTTPException(404, "Timesheet not found")
    submitter = (await db.execute(
        select(User).where(User.id == timesheet.employee_id)
    )).scalar_one_or_none()
    return timesheet, submitter


@router.patch("/{timesheet_id}/approve")
async def approve_timesheet(
    timesheet_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager),
):
    """Fill the actor's approval slot. A non-admin timesheet needs a PM plus two
    DIFFERENT admins; an admin's own timesheet needs the single admin slot. Full
    approval freezes cost."""
    timesheet, submitter = await _load_ts_and_submitter(db, timesheet_id)
    submitter_is_admin = bool(submitter and submitter.role == "admin")
    is_admin = current_user.role == "admin"

    if not is_admin and submitter_is_admin:
        raise HTTPException(403, "Not permitted to approve this timesheet")
    if timesheet.status == "rejected":
        raise HTTPException(400, "This timesheet was rejected; the employee must resubmit.")

    now = datetime.now(timezone.utc)
    if is_admin and submitter_is_admin:
        # Admin's own timesheet: single admin approval, no second factor.
        if timesheet.admin_approved_at:
            raise HTTPException(400, "Already approved by an admin")
        timesheet.admin_approved_by = current_user.id
        timesheet.admin_approved_at = now
        slot = "admin"
    elif is_admin:
        # Non-admin timesheet: needs two DIFFERENT admins. First admin fills the
        # admin slot; a second, different admin fills the second-factor slot.
        if timesheet.admin_approved_at is None:
            timesheet.admin_approved_by = current_user.id
            timesheet.admin_approved_at = now
            slot = "admin"
        elif timesheet.admin2_approved_at is None:
            if timesheet.admin_approved_by == current_user.id:
                raise HTTPException(400, "You gave the first admin approval — a different admin must give the second.")
            timesheet.admin2_approved_by = current_user.id
            timesheet.admin2_approved_at = now
            slot = "admin2"
        else:
            raise HTTPException(400, "Both admin approvals are already recorded")
    else:  # project_manager
        if timesheet.pm_approved_at:
            raise HTTPException(400, "Already approved by a project manager")
        timesheet.pm_approved_by = current_user.id
        timesheet.pm_approved_at = now
        slot = "pm"

    _recompute_status(timesheet, submitter_is_admin)
    fully_approved = timesheet.status == "approved"
    if fully_approved:
        await _freeze_entries(db, timesheet)

    who = submitter.name if submitter else "employee"
    await log_audit(db, current_user, f"timesheet.{slot}_approved", "timesheet", timesheet.id,
                    summary=f"{'Admin' if is_admin else 'PM'} approved {who}'s timesheet (week of {timesheet.week_start})")
    if fully_approved:
        await log_audit(db, current_user, "timesheet.approved", "timesheet", timesheet.id,
                        summary=f"Timesheet fully approved — {who} (week of {timesheet.week_start})")

    await db.commit()
    await db.refresh(timesheet)

    if fully_approved:
        _queue_decision_slack(background_tasks, submitter, timesheet, "approved", None)
        from app.routers.projects import _invalidate_reserve
        _invalidate_reserve()
    return timesheet


@router.patch("/{timesheet_id}/reject")
async def reject_timesheet(
    timesheet_id: int,
    data: RejectBody,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager),
):
    timesheet, submitter = await _load_ts_and_submitter(db, timesheet_id)
    submitter_is_admin = bool(submitter and submitter.role == "admin")
    if current_user.role != "admin" and submitter_is_admin:
        raise HTTPException(403, "Not permitted to reject this timesheet")
    if timesheet.status == "rejected":
        raise HTTPException(400, "Already rejected")

    was_approved = timesheet.status == "approved"
    timesheet.status = "rejected"
    timesheet.rejected_by = current_user.id
    timesheet.rejected_at = datetime.now(timezone.utc)
    timesheet.rejection_reason = data.rejection_reason

    who = submitter.name if submitter else "employee"
    await log_audit(db, current_user, "timesheet.rejected", "timesheet", timesheet.id,
                    summary=f"Rejected {who}'s timesheet (week of {timesheet.week_start})",
                    details={"reason": data.rejection_reason} if data.rejection_reason else None)

    await db.commit()
    await db.refresh(timesheet)

    _queue_decision_slack(background_tasks, submitter, timesheet, "rejected", timesheet.rejection_reason)
    if was_approved:
        from app.routers.projects import _invalidate_reserve
        _invalidate_reserve()
    return timesheet