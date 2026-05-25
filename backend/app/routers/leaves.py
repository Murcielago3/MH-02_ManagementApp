from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import date
from pydantic import BaseModel
from app.database import get_db
from app.models.leave import LeaveRequest
from app.models.user import User
from app.auth import get_current_user, require_admin, require_manager

router = APIRouter(prefix="/leaves", tags=["leaves"])

class LeaveCreate(BaseModel):
    start_date: date
    end_date: date
    reason: str

class LeaveAction(BaseModel):
    status: str

@router.get("/")
async def list_leaves(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    result = await db.execute(select(LeaveRequest).options(selectinload(LeaveRequest.employee)))
    return result.scalars().all()

@router.get("/my")
async def my_leaves(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    result = await db.execute(
        select(LeaveRequest).where(LeaveRequest.employee_id == current_user.id)
    )
    return result.scalars().all()
@router.post("/", status_code=201)
async def apply_leave(
    data: LeaveCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    days = (data.end_date - data.start_date).days + 1

    if current_user.leaves_allowed < days:
        raise HTTPException(400, f"Insufficient leaves. You have {current_user.leaves_allowed} days remaining")

    leave = LeaveRequest(
        employee_id = current_user.id,
        start_date=data.start_date,
        end_date=data.end_date,
        reason=data.reason,
        days_count=days
    )
    db.add(leave)
    await db.commit()
    await db.refresh(leave)
    return leave

@router.patch("/{leave_id}/action")
async def action_leave(
    leave_id: int,
    data: LeaveAction,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    if data.status not in ["approved", "rejected"]:
        raise HTTPException(400, "Status must be approved or rejected")

    result = await db.execute(
        select(LeaveRequest)
        .where(LeaveRequest.id == leave_id)
        .options(selectinload(LeaveRequest.employee))
    )
    leave = result.scalar_one_or_none()
    if not leave:
        raise HTTPException(404, "Leave request not found")
    if leave.days_count and leave.employee.leaves_allowed < leave.days_count:
        raise HTTPException(400, "Employee has insufficient leave balance")
    leave.status = data.status
    await db.commit()
    await db.refresh(leave)
    return leave