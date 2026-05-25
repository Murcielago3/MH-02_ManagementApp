from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import date
from pydantic import BaseModel
from app.database import get_db
from app.models.attendance import Attendance
from app.auth import get_current_user, require_manager

router = APIRouter(prefix="/attendance", tags=["attendance"])

class CheckInData(BaseModel):
    is_site_visit: bool = False
    site_name: Optional[str] = None
    site_timing: Optional[str] = None

class CheckOutData(BaseModel):
    check_out: str  # HH:MM

@router.post("/checkin", status_code=201)
async def check_in(
    data: CheckInData,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    from datetime import datetime
    today = date.today()

    # Check if already checked in today
    existing = await db.execute(
        select(Attendance).where(
            Attendance.employee_id == current_user.id,
            Attendance.date == today
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Already checked in today")

    attendance = Attendance(
        employee_id=current_user.id,
        date=today,
        check_in=datetime.now().strftime("%H:%M"),
        is_site_visit=data.is_site_visit,
        site_name=data.site_name,
        site_timing=data.site_timing
    )
    db.add(attendance)
    await db.commit()
    await db.refresh(attendance)
    return attendance

@router.patch("/checkout")
async def check_out(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    from datetime import datetime
    today = date.today()

    result = await db.execute(
        select(Attendance).where(
            Attendance.employee_id == current_user.id,
            Attendance.date == today
        )
    )
    attendance = result.scalar_one_or_none()
    if not attendance:
        raise HTTPException(400, "No check-in found for today")
    if attendance.check_out:
        raise HTTPException(400, "Already checked out today")

    attendance.check_out = datetime.now().strftime("%H:%M")
    await db.commit()
    await db.refresh(attendance)
    return attendance

@router.get("/")
async def list_attendance(
    employee_id: Optional[int] = None,
    date_filter: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    query = select(Attendance)
    if employee_id:
        query = query.where(Attendance.employee_id == employee_id)
    if date_filter:
        query = query.where(Attendance.date == date_filter)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/my")
async def my_attendance(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    result = await db.execute(
        select(Attendance).where(Attendance.employee_id == current_user.id)
    )
    return result.scalars().all()

@router.get("/today")
async def today_attendance(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    today = date.today()
    result = await db.execute(
        select(Attendance).where(Attendance.date == today)
    )
    return result.scalars().all()