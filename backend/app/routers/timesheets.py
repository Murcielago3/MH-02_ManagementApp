from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import date
from pydantic import BaseModel
from app.database import get_db
from app.models.timesheet import Timesheet
from app.models.user import User
from app.auth import get_current_user, require_manager
from app.models.timesheet import Timesheet

router = APIRouter(prefix="/timesheets", tags=["timesheets"])

class TimesheetCreate(BaseModel):
    project_id: int
    date: date
    hours_logged: float
    notes: Optional[str] = None

class TimesheetUpdate(BaseModel):
    hours_logged: Optional[float] = None
    notes: Optional[str] = None

@router.get("/")
async def list_timesheets(
    employee_id: Optional[int] = None,
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Timesheet)
    if employee_id:
        query = query.where(Timesheet.employee_id == employee_id)
    if project_id:
        query = query.where(Timesheet.project_id == project_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/my")
async def my_timesheets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Timesheet).where(Timesheet.employee_id == current_user.id)
        )
    return result.scalars().all()

@router.get("/project/{project_id}/summary")
async def project_timesheet_summary(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Timesheet.employee_id, func.sum(Timesheet.hours_logged))
        .where(Timesheet.project_id == project_id)
        .group_by(Timesheet.employee_id)
    )
    rows = result.all()
    total_result = await db.execute(
        select(func.sum(Timesheet.hours_logged))
        .where(Timesheet.project_id == project_id)
    )
    total_hours = total_result.scalar() or 0
    return {
        "project_id": project_id,
        "total_hours": float(total_hours),
        "breakdown": [
            {"employee_id": row[0], "hours": float(row[1])}
            for row in rows
        ]
    }

@router.post("/", status_code=201)
async def log_hours(
    data: TimesheetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = await db.execute(
        select(Timesheet).where(
            Timesheet.employee_id == current_user.id,
            Timesheet.project_id == data.project_id,
            Timesheet.date == data.date
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Timesheet entry already exists for this date and project")
    
    entry = Timesheet(
        employee_id=current_user.id,
        project_id=data.project_id,
        date=data.date,
        hours_logged=data.hours_logged,
        notes=data.notes
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry

@router.put("/{timesheet_id}")
async def update_timesheet(
    timesheet_id: int,
    data: TimesheetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Timesheet).where(Timesheet.id == timesheet_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Timesheet entry not found")
    if entry.employee_id != current_user.id and not current_user.is_manager:
        raise HTTPException(status_code=403, detail="Not authorized to update this timesheet")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    
    await db.commit()
    await db.refresh(entry)
    return entry

@router.delete("/{timesheet_id}", status_code=204)
async def delete_timesheet(
    timesheet_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Timesheet).where(Timesheet.id == timesheet_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Timesheet entry not found")
    if entry.employee_id != current_user.id and not current_user.is_manager:
        raise HTTPException(status_code=403, detail="Not authorized to delete this timesheet")
    
    await db.delete(entry)
    await db.commit()