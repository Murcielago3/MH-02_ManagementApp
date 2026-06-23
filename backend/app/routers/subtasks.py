from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from pydantic import BaseModel
from app.database import get_db
from app.models import Subtask, Task, User
from app.auth import get_current_user, require_manager

router = APIRouter(prefix="/tasks/{task_id}/subtasks", tags=["subtasks"])


class SubtaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    duration_hours: Optional[float] = None


class SubtaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duration_hours: Optional[float] = None
    status: Optional[str] = None


def _serialize(s: Subtask) -> dict:
    return {
        "id": s.id,
        "task_id": s.task_id,
        "title": s.title,
        "description": s.description,
        "duration_hours": float(s.duration_hours) if s.duration_hours is not None else None,
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
    s = Subtask(
        task_id=task_id,
        title=data.title.strip(),
        description=data.description,
        duration_hours=data.duration_hours,
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
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
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
