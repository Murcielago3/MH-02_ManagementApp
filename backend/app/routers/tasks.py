from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import date as date_type
from pydantic import BaseModel
from app.database import get_db
from app.models import Task, User
from app.auth import get_current_user, require_manager

router = APIRouter(prefix="/tasks", tags=["tasks"])

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
    return result.scalars().all()

@router.get("/my")
async def my_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Task).where(Task.assigned_to == current_user.id)
    result = await db.execute(query)
    return result.scalars().all()

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

    return [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "date": str(t.date),
            "end_date": str(t.end_date) if t.end_date else None,
            "duration_hours": t.duration_hours,
            "priority": t.priority,
            "status": t.status,
            "assigned_to": t.assigned_to,
            "assigned_by": t.assigned_by,
            "project_id": t.project_id,
        }
        for t in tasks
    ]

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
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, parse_task_update_value(task, field, value))
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
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, parse_task_update_value(task, field, value))
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

