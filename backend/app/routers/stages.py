"""Project stages and stage subtasks.

Money/hours per stage are DERIVED, never stored:

    bucket        = project_remuneration   (the full agreed value)
    stage.amount  = percentage% of bucket
    stage.hours   = percentage% of total_assigned_hours

so correcting a project's value or hour budget keeps every stage consistent.
The advance is NOT deducted: a stage's percentage is of the whole project cost,
and the advance is tracked separately on the project.

Permissions
    stages          - admin only (create / update / delete / mark complete)
    stage subtasks  - admin or project manager (CRUD + mark complete)
    reading         - any authenticated employee (it's a studio-wide todo list)
"""
from datetime import date as date_type, datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user, require_admin, require_manager
from app.database import get_db
from app.models.project import Project
from app.models.project_stage import ProjectStage, StageSubtask
from app.models.user import User
from app.models.weekly_timesheet import WeeklyTimesheet, WeeklyTimesheetEntry
from app.services.audit import log_audit

router = APIRouter(tags=["project-stages"])

# A stage allocation may not exceed the project's remaining bucket.
FULL = Decimal("100")


# ─────────────────────────── schemas ───────────────────────────
class StageCreate(BaseModel):
    name: str
    percentage: float


class StageUpdate(BaseModel):
    name: Optional[str] = None
    percentage: Optional[float] = None
    status: Optional[str] = None
    sequence: Optional[int] = None


class SubtaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[date_type] = None


class SubtaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date_type] = None
    status: Optional[str] = None
    stage_id: Optional[int] = None


# ─────────────────────────── helpers ───────────────────────────
def _q(v) -> Decimal:
    return Decimal(str(v or 0))


def project_bucket(project: Project) -> Decimal:
    """The amount stages divide up: the full agreed project value. The advance
    is NOT deducted (it's tracked separately on the project)."""
    bucket = _q(project.project_remuneration)
    return bucket if bucket > 0 else Decimal("0")


def _serialize_subtask(s: StageSubtask, worker_names: Optional[list] = None) -> dict:
    today = date_type.today()
    overdue = bool(
        s.due_date and s.status != "completed" and s.due_date < today
    )
    return {
        "id": s.id,
        "stage_id": s.stage_id,
        "project_id": s.project_id,
        "title": s.title,
        "description": s.description,
        "due_date": str(s.due_date) if s.due_date else None,
        "status": s.status,
        "is_overdue": overdue,
        "days_overdue": (today - s.due_date).days if overdue else 0,
        "started_at": s.started_at.isoformat() if s.started_at else None,
        "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        "completed_by": s.completed_by,
        "created_by": s.created_by,
        "created_by_role": s.created_by_role,
        # Who has logged timesheet hours against this subtask.
        "workers": worker_names if worker_names is not None else [],
    }


def _serialize_stage(st: ProjectStage, project: Project, workers_by_subtask=None) -> dict:
    bucket = project_bucket(project)
    pct = _q(st.percentage)
    total_hours = _q(project.total_assigned_hours)

    subs = list(st.subtasks or [])
    done = sum(1 for s in subs if s.status == "completed")
    # Completion is driven by subtasks; a stage with none sits at 0% until it is
    # explicitly marked complete.
    if subs:
        completion = round(done / len(subs) * 100, 1)
    else:
        completion = 100.0 if st.status == "completed" else 0.0

    return {
        "id": st.id,
        "project_id": st.project_id,
        "name": st.name,
        "sequence": st.sequence,
        "percentage": float(pct),
        # Derived - see module docstring.
        "amount": float((bucket * pct / FULL).quantize(Decimal("0.01"))),
        "hours": float((total_hours * pct / FULL).quantize(Decimal("0.01"))),
        "status": st.status,
        "completion_percent": completion,
        "subtask_total": len(subs),
        "subtask_completed": done,
        "completed_at": st.completed_at.isoformat() if st.completed_at else None,
        "completed_by": st.completed_by,
        "created_by": st.created_by,
        "created_by_role": st.created_by_role,
        "subtasks": [
            _serialize_subtask(s, (workers_by_subtask or {}).get(s.id, []))
            for s in subs
        ],
    }


async def _load_project(db: AsyncSession, project_id: int) -> Project:
    p = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Project not found")
    return p


async def _load_stages(db: AsyncSession, project_id: int):
    return (await db.execute(
        select(ProjectStage)
        .options(selectinload(ProjectStage.subtasks))
        .where(ProjectStage.project_id == project_id)
        .order_by(ProjectStage.sequence, ProjectStage.id)
    )).scalars().all()


async def _allocated_pct(db: AsyncSession, project_id: int, exclude_stage_id: int | None = None) -> Decimal:
    q = select(func.coalesce(func.sum(ProjectStage.percentage), 0)).where(
        ProjectStage.project_id == project_id
    )
    if exclude_stage_id is not None:
        q = q.where(ProjectStage.id != exclude_stage_id)
    return _q((await db.execute(q)).scalar_one())


async def _workers_by_subtask(db: AsyncSession, project_id: int) -> dict:
    """{subtask_id: [employee names]} from approved timesheet entries, so the
    stages view can show who actually worked on each subtask."""
    rows = (await db.execute(
        select(WeeklyTimesheetEntry.subtask_id, User.name, func.sum(WeeklyTimesheetEntry.hours))
        .join(WeeklyTimesheet, WeeklyTimesheet.id == WeeklyTimesheetEntry.timesheet_id)
        .join(User, User.id == WeeklyTimesheet.employee_id)
        .where(
            WeeklyTimesheetEntry.project_id == project_id,
            WeeklyTimesheetEntry.subtask_id.isnot(None),
        )
        .group_by(WeeklyTimesheetEntry.subtask_id, User.name)
    )).all()
    out: dict = {}
    for subtask_id, name, hours in rows:
        out.setdefault(subtask_id, []).append({"name": name, "hours": float(hours or 0)})
    for v in out.values():
        v.sort(key=lambda w: -w["hours"])
    return out


# ─────────────────────────── stage endpoints ───────────────────────────
@router.get("/projects/{project_id}/stages")
async def list_stages(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stages with derived money/hours plus the remaining unallocated bucket."""
    project = await _load_project(db, project_id)
    stages = await _load_stages(db, project_id)
    workers = await _workers_by_subtask(db, project_id)

    bucket = project_bucket(project)
    allocated = sum((_q(s.percentage) for s in stages), Decimal("0"))
    remaining_pct = FULL - allocated

    return {
        "project_id": project_id,
        "project_name": project.name,
        "total_cost": float(_q(project.project_remuneration)),
        "advance_amount": float(_q(project.advance_amount)),
        "bucket": float(bucket),
        "total_hours": float(_q(project.total_assigned_hours)),
        "allocated_percent": float(allocated),
        "remaining_percent": float(remaining_pct),
        "remaining_amount": float((bucket * remaining_pct / FULL).quantize(Decimal("0.01"))),
        "remaining_hours": float(
            (_q(project.total_assigned_hours) * remaining_pct / FULL).quantize(Decimal("0.01"))
        ),
        "stages": [_serialize_stage(s, project, workers) for s in stages],
    }


@router.post("/projects/{project_id}/stages", status_code=201)
async def create_stage(
    project_id: int,
    data: StageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    project = await _load_project(db, project_id)
    if not data.name or not data.name.strip():
        raise HTTPException(400, "Stage name is required")
    pct = _q(data.percentage)
    if pct <= 0:
        raise HTTPException(400, "Percentage must be greater than 0")

    allocated = await _allocated_pct(db, project_id)
    if allocated + pct > FULL:
        raise HTTPException(
            400,
            f"Only {float(FULL - allocated):g}% of the project is left to allocate - "
            f"{float(pct):g}% would take the total to {float(allocated + pct):g}%.",
        )

    seq = (await db.execute(
        select(func.coalesce(func.max(ProjectStage.sequence), -1)).where(
            ProjectStage.project_id == project_id
        )
    )).scalar_one()

    stage = ProjectStage(
        project_id=project_id,
        name=data.name.strip(),
        percentage=pct,
        sequence=int(seq) + 1,
        created_by=current_user.id,
        created_by_role=current_user.role,
    )
    db.add(stage)
    await db.flush()
    await log_audit(db, current_user, "stage.created", "project", project_id,
                    summary=f"Added stage '{stage.name}' ({float(pct):g}%) to {project.name}")
    await db.commit()
    await db.refresh(stage, ["subtasks"])
    return _serialize_stage(stage, project)


@router.patch("/stages/{stage_id}")
async def update_stage(
    stage_id: int,
    data: StageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    stage = (await db.execute(
        select(ProjectStage).options(selectinload(ProjectStage.subtasks))
        .where(ProjectStage.id == stage_id)
    )).scalar_one_or_none()
    if not stage:
        raise HTTPException(404, "Stage not found")
    project = await _load_project(db, stage.project_id)

    fields = data.model_dump(exclude_unset=True)
    if "percentage" in fields:
        pct = _q(fields["percentage"])
        if pct <= 0:
            raise HTTPException(400, "Percentage must be greater than 0")
        allocated = await _allocated_pct(db, stage.project_id, exclude_stage_id=stage_id)
        if allocated + pct > FULL:
            raise HTTPException(
                400,
                f"Only {float(FULL - allocated):g}% is available for this stage - "
                f"{float(pct):g}% would take the project to {float(allocated + pct):g}%.",
            )
        stage.percentage = pct
    if "name" in fields and fields["name"]:
        stage.name = fields["name"].strip()
    if "sequence" in fields and fields["sequence"] is not None:
        stage.sequence = fields["sequence"]
    if "status" in fields and fields["status"]:
        if fields["status"] not in ("active", "completed"):
            raise HTTPException(400, "Status must be 'active' or 'completed'")
        stage.status = fields["status"]
        if stage.status == "completed":
            stage.completed_at = datetime.now()
            stage.completed_by = current_user.id
        else:
            stage.completed_at = None
            stage.completed_by = None

    await log_audit(db, current_user, "stage.updated", "project", stage.project_id,
                    summary=f"Updated stage '{stage.name}' on {project.name}")
    await db.commit()
    await db.refresh(stage, ["subtasks"])
    return _serialize_stage(stage, project)


@router.delete("/stages/{stage_id}", status_code=204)
async def delete_stage(
    stage_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    stage = (await db.execute(select(ProjectStage).where(ProjectStage.id == stage_id))).scalar_one_or_none()
    if not stage:
        raise HTTPException(404, "Stage not found")
    await log_audit(db, current_user, "stage.deleted", "project", stage.project_id,
                    summary=f"Deleted stage '{stage.name}'")
    await db.delete(stage)
    await db.commit()


# ─────────────────────────── subtask endpoints ───────────────────────────
@router.get("/projects/{project_id}/stage-subtasks")
async def list_project_subtasks(
    project_id: int,
    open_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Every stage subtask on a project - the studio-wide todo list that feeds
    the timesheet picker and the employee project view."""
    q = select(StageSubtask, ProjectStage.name).join(
        ProjectStage, ProjectStage.id == StageSubtask.stage_id
    ).where(StageSubtask.project_id == project_id)
    if open_only:
        q = q.where(StageSubtask.status != "completed")
    rows = (await db.execute(q.order_by(ProjectStage.sequence, StageSubtask.id))).all()
    out = []
    for s, stage_name in rows:
        d = _serialize_subtask(s)
        d["stage_name"] = stage_name
        out.append(d)
    return out


@router.post("/stages/{stage_id}/subtasks", status_code=201)
async def create_subtask(
    stage_id: int,
    data: SubtaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    """Admins and project managers may add subtasks to a stage."""
    stage = (await db.execute(select(ProjectStage).where(ProjectStage.id == stage_id))).scalar_one_or_none()
    if not stage:
        raise HTTPException(404, "Stage not found")
    if not data.title or not data.title.strip():
        raise HTTPException(400, "Title is required")

    s = StageSubtask(
        stage_id=stage_id,
        project_id=stage.project_id,
        title=data.title.strip(),
        description=data.description,
        due_date=data.due_date,
        created_by=current_user.id,
        created_by_role=current_user.role,
    )
    db.add(s)
    await db.flush()
    await log_audit(db, current_user, "stage_subtask.created", "project", stage.project_id,
                    summary=f"Added subtask '{s.title}' to stage '{stage.name}'")
    await db.commit()
    await db.refresh(s)
    return _serialize_subtask(s)


@router.patch("/stage-subtasks/{subtask_id}")
async def update_subtask(
    subtask_id: int,
    data: SubtaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    """Admins and PMs may edit a subtask or mark it complete."""
    s = (await db.execute(select(StageSubtask).where(StageSubtask.id == subtask_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Subtask not found")

    fields = data.model_dump(exclude_unset=True)
    for k in ("title", "description", "due_date", "stage_id"):
        if k in fields:
            setattr(s, k, fields[k].strip() if k == "title" and fields[k] else fields[k])

    if "status" in fields:
        if fields["status"] not in ("pending", "in-progress", "completed"):
            raise HTTPException(400, "Invalid status")
        s.status = fields["status"]
        now = datetime.now()
        if s.status == "completed":
            s.completed_at = s.completed_at or now
            s.started_at = s.started_at or now
            s.completed_by = current_user.id
        else:
            # Reopening clears completion so stage % completion drops back.
            s.completed_at = None
            s.completed_by = None
            if s.status == "in-progress" and s.started_at is None:
                s.started_at = now

    await db.commit()
    await db.refresh(s)
    return _serialize_subtask(s)


@router.delete("/stage-subtasks/{subtask_id}", status_code=204)
async def delete_subtask(
    subtask_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    s = (await db.execute(select(StageSubtask).where(StageSubtask.id == subtask_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Subtask not found")
    await db.delete(s)
    await db.commit()


# ─────────────────────── employee-facing helpers ───────────────────────
@router.get("/my/stage-subtask-deadlines")
async def my_subtask_deadlines(
    start_date: Optional[date_type] = None,
    end_date: Optional[date_type] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Subtask deadlines for the calendar.

    Stage subtasks are a studio-wide todo list: every employee can see what is
    open on any project and pick it on their timesheet, so these are NOT scoped
    to project assignment. (An earlier version filtered by ProjectAssignment,
    which hid every deadline from employees - projects are staffed via teams,
    so that table is largely empty.)
    """
    q = (
        select(StageSubtask, ProjectStage.name, Project.name, Project.color)
        .join(ProjectStage, ProjectStage.id == StageSubtask.stage_id)
        .join(Project, Project.id == StageSubtask.project_id)
        .where(StageSubtask.due_date.isnot(None))
    )
    if start_date:
        q = q.where(StageSubtask.due_date >= start_date)
    if end_date:
        q = q.where(StageSubtask.due_date <= end_date)

    rows = (await db.execute(q.order_by(StageSubtask.due_date))).all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "due_date": str(s.due_date),
            "status": s.status,
            "stage_id": s.stage_id,
            "stage_name": stage_name,
            "project_id": s.project_id,
            "project_name": project_name,
            "color": color or "#287475",
            "is_overdue": s.status != "completed" and s.due_date < date_type.today(),
        }
        for s, stage_name, project_name, color in rows
    ]
