from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date as date_type
from pydantic import BaseModel
from app.database import get_db
from app.models.holiday import Holiday
from app.auth import get_current_user, require_admin

router = APIRouter(prefix="/holidays", tags=["holidays"])


class HolidayCreate(BaseModel):
    date: date_type
    name: str


def _serialize(h: Holiday) -> dict:
    return {"id": h.id, "date": str(h.date), "name": h.name}


@router.get("/")
async def list_holidays(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),  # any authenticated user can read
):
    result = await db.execute(select(Holiday).order_by(Holiday.date))
    return [_serialize(h) for h in result.scalars().all()]


@router.post("/", status_code=201)
async def create_holiday(
    data: HolidayCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    # Upsert: if a holiday already exists for that date, just update its name.
    existing = await db.execute(select(Holiday).where(Holiday.date == data.date))
    h = existing.scalar_one_or_none()
    if h:
        h.name = data.name
    else:
        h = Holiday(date=data.date, name=data.name)
        db.add(h)
    await db.commit()
    await db.refresh(h)
    return _serialize(h)


@router.delete("/{holiday_id}", status_code=204)
async def delete_holiday(
    holiday_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    result = await db.execute(select(Holiday).where(Holiday.id == holiday_id))
    h = result.scalar_one_or_none()
    if not h:
        raise HTTPException(404, "Holiday not found")
    await db.delete(h)
    await db.commit()
