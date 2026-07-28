from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from datetime import date as date_type
from pydantic import BaseModel
from app.database import get_db
from app.models import Task, User, Subtask
from app.auth import get_current_user, require_manager

router = APIRouter(prefix="/tasks", tags=["tasks"])


async def subtask_overdue_map(db: AsyncSession, task_ids: list) -> dict:
    """{task_id: {"overdue_subtasks": n, "subtask_delay_days": worst}} for the
    given tasks. Overdue = an unfinished subtask whose deadline has passed.
    Parent-task deadlines are deliberately not considered here."""
    if not task_ids:
        return {}
    today = date_type.today()
    rows = (await db.execute(
        select(Subtask.task_id, Subtask.due_date).where(
            Subtask.task_id.in_(task_ids),
            Subtask.due_date.isnot(None),
            Subtask.due_date < today,
            Subtask.status != "completed",
        )
    )).all()
    out = {}
    for task_id, due in rows:
        entry = out.setdefault(task_id, {"overdue_subtasks": 0, "subtask_delay_days": 0})
        entry["overdue_subtasks"] += 1
        entry["subtask_delay_days"] = max(entry["subtask_delay_days"], (today - due).days)
    return out


def with_subtask_delay(task: Task, overdue: dict) -> dict:
    info = overdue.get(task.id)
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "date": str(task.date),
        "end_date": str(task.end_date) if task.end_date else None,
        "duration_hours": task.duration_hours,
        "priority": task.priority,
        "status": task.status,
        "project_id": task.project_id,
        "assigned_to": task.assigned_to,
        "assigned_by": task.assigned_by,
        "overdue_subtasks": info["overdue_subtasks"] if info else 0,
        "subtask_delay_days": info["subtask_delay_days"] if info else 0,
    }

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    date: date_type
    duration_hours: Optional[int] = None
    priority: str = "medium"
    assigned_to: int
    project_id: Optional[int] = None
    end_date: Optional[date_type] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    duration_hours: Optional[int] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    project_id: Optional[int] = None
    end_date: Optional[date_type] = None
    assigned_to: Optional[int] = None

@router.get("/")
async def list_tasks(
    employee_id: Optional[int] = None,
    project_id: Optional[int] = None,
    date_filter: Optional[date_type] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Task)
    if employee_id:
        query = query.where(Task.assigned_to == employee_id)
    if project_id:
        query = query.where(Task.project_id == project_id)
    if date_filter:
        query = query.where(Task.date == date_filter)

    result = await db.execute(query)
    tasks = result.scalars().all()
    overdue = await subtask_overdue_map(db, [t.id for t in tasks])
    return [with_subtask_delay(t, overdue) for t in tasks]

@router.get("/my")
async def my_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Task).where(Task.assigned_to == current_user.id)
    result = await db.execute(query)
    tasks = result.scalars().all()
    overdue = await subtask_overdue_map(db, [t.id for t in tasks])
    return [with_subtask_delay(t, overdue) for t in tasks]

@router.get("/calendar")
async def calendar_tasks(
    year: Optional[int] = None,
    month: Optional[int] = None,
    start_date: Optional[date_type] = None,
    end_date: Optional[date_type] = None,
    employee_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """
    Returns tasks overlapping the requested window. Accepts either:
      - explicit start_date + end_date (preferred — handles month-straddling windows)
      - year + month (legacy fallback — fetches the whole month)
    """
    from datetime import date as dt
    import calendar

    if start_date and end_date:
        first_day = start_date
        last_day = end_date
    elif year and month:
        first_day = dt(year, month, 1)
        last_day = dt(year, month, calendar.monthrange(year, month)[1])
    else:
        raise HTTPException(400, "Provide either (start_date + end_date) or (year + month).")

    # Tasks overlapping the window: start in window, end in window, or span the window
    from sqlalchemy import or_, and_
    query = select(Task).where(
        or_(
            and_(Task.date >= first_day, Task.date <= last_day),
            and_(Task.end_date >= first_day, Task.end_date <= last_day),
            and_(Task.date <= first_day, Task.end_date >= last_day),
        )
    )
    if employee_id:
        query = query.where(Task.assigned_to == employee_id)
    result = await db.execute(query)
    tasks = result.scalars().all()

    overdue = await subtask_overdue_map(db, [t.id for t in tasks])
    return [with_subtask_delay(t, overdue) for t in tasks]

@router.post("/", status_code=201)
async def create_task(
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    task = Task(
        title=data.title,
        description=data.description,
        date=data.date,
        end_date=data.end_date,
        duration_hours=data.duration_hours,
        priority=data.priority,
        project_id=data.project_id,
        assigned_to=data.assigned_to,
        assigned_by=current_user.id
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


class BulkTaskAssign(BaseModel):
    title: str
    description: Optional[str] = None
    date: date_type
    end_date: Optional[date_type] = None
    duration_hours: Optional[int] = None
    priority: str = "medium"
    project_id: Optional[int] = None
    assigned_to: List[int]   # one task is created per employee id


@router.post("/bulk-assign", status_code=201)
async def bulk_assign(
    data: BulkTaskAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Assign a project (as a task) to several employees at once — one Task row
    per selected employee. Powers the 'Assign Project' button."""
    if not data.assigned_to:
        raise HTTPException(400, "Select at least one employee")
    created = []
    for emp_id in data.assigned_to:
        task = Task(
            title=data.title,
            description=data.description,
            date=data.date,
            end_date=data.end_date,
            duration_hours=data.duration_hours,
            priority=data.priority,
            project_id=data.project_id,
            assigned_to=emp_id,
            assigned_by=current_user.id,
        )
        db.add(task)
        created.append(task)
    await db.commit()
    return {"created": len(created)}

def _stamp_task_transition(task):
    """Record when a task started / completed, for the quarterly report.
    Reopening clears the completion stamp so it stops counting as delivered."""
    from datetime import datetime
    now = datetime.now()
    if task.status == "completed":
        if task.completed_at is None:
            task.completed_at = now
        if task.started_at is None:
            task.started_at = now
    else:
        task.completed_at = None
        if task.status == "in-progress" and task.started_at is None:
            task.started_at = now


def parse_task_update_value(task, field, value):
    if field in ["date", "end_date"]:
        if value is None:
            return None
        if isinstance(value, date_type):
            return value
        try:
            return date_type.fromisoformat(value)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail=f"Invalid date format for {field}. Use YYYY-MM-DD.")
    return value

@router.put("/{task_id}")
async def update_task(
    task_id: int,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    fields = data.model_dump(exclude_unset=True)
    for field, value in fields.items():
        setattr(task, field, parse_task_update_value(task, field, value))
    if "status" in fields:
        _stamp_task_transition(task)
    await db.commit()
    await db.refresh(task)
    return task

@router.patch("/{task_id}")
async def patch_task(
    task_id: int,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    fields = data.model_dump(exclude_unset=True)
    for field, value in fields.items():
        setattr(task, field, parse_task_update_value(task, field, value))
    if "status" in fields:
        _stamp_task_transition(task)
    await db.commit()
    await db.refresh(task)
    return task

class StatusUpdate(BaseModel):
    status: str

@router.patch("/{task_id}/status")
async def update_task_status(
    task_id: int,
    data: StatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if data.status not in ["pending", "in-progress", "completed"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if current_user.role == "employee" and task.assigned_to != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own tasks")
    task.status = data.status
    _stamp_task_transition(task)
    await db.commit()
    await db.refresh(task)
    return task

@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(task)
    await db.commit()

