from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import date as date_type, datetime
from pydantic import BaseModel
from app.database import get_db
from app.models import Subtask, Task, User
from app.auth import get_current_user, require_manager

router = APIRouter(prefix="/tasks/{task_id}/subtasks", tags=["subtasks"])


class SubtaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: date_type
    # Defaults to the day the subtask is assigned; only sent when backdating.
    start_date: Optional[date_type] = None


class SubtaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date_type] = None
    due_date: Optional[date_type] = None
    status: Optional[str] = None


def _serialize(s: Subtask) -> dict:
    today = date_type.today()
    days_overdue = 0
    if s.due_date and s.status != "completed" and s.due_date < today:
        days_overdue = (today - s.due_date).days
    return {
        "id": s.id,
        "task_id": s.task_id,
        "title": s.title,
        "description": s.description,
        "start_date": str(s.start_date) if s.start_date else None,
        "due_date": str(s.due_date) if s.due_date else None,
        "days_overdue": days_overdue,
        "is_overdue": days_overdue > 0,
        "started_at": s.started_at.isoformat() if s.started_at else None,
        "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        "status": s.status,
        "created_by": s.created_by,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


@router.get("/")
async def list_subtasks(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Subtask).where(Subtask.task_id == task_id).order_by(Subtask.created_at.asc())
    )
    return [_serialize(s) for s in result.scalars().all()]


@router.post("/", status_code=201)
async def create_subtask(
    task_id: int,
    data: SubtaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parent = (await db.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()
    if not parent:
        raise HTTPException(404, "Parent task not found")
    # Allow the assignee or any manager to add a subtask
    if current_user.role == "employee" and parent.assigned_to != current_user.id:
        raise HTTPException(403, "Only the assignee or a manager can add subtasks")
    if not data.title or not data.title.strip():
        raise HTTPException(400, "Title required")
    # The subtask window opens the day it's assigned, not the parent task's start.
    start = data.start_date or date_type.today()
    if data.due_date < start:
        raise HTTPException(400, "Deadline cannot be before the date the subtask is assigned")
    s = Subtask(
        task_id=task_id,
        title=data.title.strip(),
        description=data.description,
        start_date=start,
        due_date=data.due_date,
        created_by=current_user.id,
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return _serialize(s)


# Endpoints to update/delete an individual subtask — mounted on a separate
# router prefix so the {subtask_id} path param doesn't collide with the
# parent-scoped list/create above.
single_router = APIRouter(prefix="/subtasks", tags=["subtasks"])


@single_router.patch("/{subtask_id}")
async def update_subtask(
    subtask_id: int,
    data: SubtaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = (await db.execute(select(Subtask).where(Subtask.id == subtask_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Subtask not found")
    parent = (await db.execute(select(Task).where(Task.id == s.task_id))).scalar_one_or_none()
    if current_user.role == "employee" and parent and parent.assigned_to != current_user.id:
        raise HTTPException(403, "Not authorised")
    fields = data.model_dump(exclude_unset=True)
    for k, v in fields.items():
        setattr(s, k, v)
    if s.due_date and s.start_date and s.due_date < s.start_date:
        raise HTTPException(400, "Deadline cannot be before the date the subtask is assigned")

    # Stamp transitions so the quarterly report can tell on-time from late, and
    # started from never-started. Un-completing clears the stamp so a reopened
    # subtask isn't still counted as delivered.
    if "status" in fields:
        now = datetime.now()
        if s.status == "completed":
            if s.completed_at is None:
                s.completed_at = now
            if s.started_at is None:
                s.started_at = now
        else:
            s.completed_at = None
            if s.status == "in-progress" and s.started_at is None:
                s.started_at = now

    await db.commit()
    await db.refresh(s)
    return _serialize(s)


@single_router.delete("/{subtask_id}", status_code=204)
async def delete_subtask(
    subtask_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = (await db.execute(select(Subtask).where(Subtask.id == subtask_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Subtask not found")
    parent = (await db.execute(select(Task).where(Task.id == s.task_id))).scalar_one_or_none()
    if current_user.role == "employee" and parent and parent.assigned_to != current_user.id:
        raise HTTPException(403, "Not authorised")
    await db.delete(s)
    await db.commit()
