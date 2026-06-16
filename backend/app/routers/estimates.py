from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import date
from pydantic import BaseModel
from app.database import get_db
from app.models.estimate import Estimate, EstimateEmployee
from app.auth import get_current_user, require_admin

router = APIRouter(prefix="/estimates", tags=["estimates"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class EstimateEmployeeIn(BaseModel):
    emp_type: str
    base_pay: float
    hrs_per_day: float = 8
    pay_per_hour: float = 0
    total_hours: float = 0
    total_cost: float = 0


class EstimateCreate(BaseModel):
    project_name: str
    start_date: date
    end_date: date
    working_days: int = 0
    partner_pay_per_hour: float = 0
    partner_cost: float = 0
    team_cost: float = 0
    grand_total: float = 0
    project_color: str = "#287475"
    status: str = "draft"
    employees: List[EstimateEmployeeIn] = []


class EstimateUpdate(BaseModel):
    project_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    working_days: Optional[int] = None
    partner_pay_per_hour: Optional[float] = None
    partner_cost: Optional[float] = None
    team_cost: Optional[float] = None
    grand_total: Optional[float] = None
    project_color: Optional[str] = None
    status: Optional[str] = None
    employees: Optional[List[EstimateEmployeeIn]] = None


class EstimateEmployeeOut(BaseModel):
    id: int
    emp_type: str
    base_pay: float
    hrs_per_day: float
    pay_per_hour: float
    total_hours: float
    total_cost: float

    class Config:
        from_attributes = True


class EstimateOut(BaseModel):
    id: int
    project_name: str
    start_date: date
    end_date: date
    working_days: int
    partner_pay_per_hour: float
    partner_cost: float
    team_cost: float
    grand_total: float
    project_color: str
    status: str
    created_by: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    employees: List[EstimateEmployeeOut] = []

    class Config:
        from_attributes = True


# ── Helper to serialize datetimes ─────────────────────────────────────────────

def serialize_estimate(est: Estimate) -> dict:
    return {
        "id": est.id,
        "project_name": est.project_name,
        "start_date": est.start_date.isoformat() if est.start_date else None,
        "end_date": est.end_date.isoformat() if est.end_date else None,
        "working_days": est.working_days,
        "partner_pay_per_hour": float(est.partner_pay_per_hour or 0),
        "partner_cost": float(est.partner_cost or 0),
        "team_cost": float(est.team_cost or 0),
        "grand_total": float(est.grand_total or 0),
        "project_color": est.project_color or "#287475",
        "status": est.status or "draft",
        "created_by": est.created_by,
        "created_at": est.created_at.isoformat() if est.created_at else None,
        "updated_at": est.updated_at.isoformat() if est.updated_at else None,
        "employees": [
            {
                "id": e.id,
                "emp_type": e.emp_type,
                "base_pay": float(e.base_pay or 0),
                "hrs_per_day": float(e.hrs_per_day or 0),
                "pay_per_hour": float(e.pay_per_hour or 0),
                "total_hours": float(e.total_hours or 0),
                "total_cost": float(e.total_cost or 0),
            }
            for e in (est.employees or [])
        ],
    }


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/")
async def list_estimates(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    result = await db.execute(
        select(Estimate)
        .options(selectinload(Estimate.employees))
        .order_by(Estimate.updated_at.desc())
    )
    estimates = result.scalars().all()
    return [serialize_estimate(e) for e in estimates]


@router.get("/{estimate_id}")
async def get_estimate(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    result = await db.execute(
        select(Estimate)
        .options(selectinload(Estimate.employees))
        .where(Estimate.id == estimate_id)
    )
    est = result.scalar_one_or_none()
    if not est:
        raise HTTPException(404, "Estimate not found")
    return serialize_estimate(est)


@router.post("/", status_code=201)
async def create_estimate(
    data: EstimateCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    est = Estimate(
        project_name=data.project_name,
        start_date=data.start_date,
        end_date=data.end_date,
        working_days=data.working_days,
        partner_pay_per_hour=data.partner_pay_per_hour,
        partner_cost=data.partner_cost,
        team_cost=data.team_cost,
        grand_total=data.grand_total,
        project_color=data.project_color,
        status=data.status,
        created_by=current_user.id,
    )

    for emp in data.employees:
        est.employees.append(
            EstimateEmployee(
                emp_type=emp.emp_type,
                base_pay=emp.base_pay,
                hrs_per_day=emp.hrs_per_day,
                pay_per_hour=emp.pay_per_hour,
                total_hours=emp.total_hours,
                total_cost=emp.total_cost,
            )
        )

    db.add(est)
    await db.commit()
    await db.refresh(est, attribute_names=["employees"])
    return serialize_estimate(est)


@router.put("/{estimate_id}")
async def update_estimate(
    estimate_id: int,
    data: EstimateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    result = await db.execute(
        select(Estimate)
        .options(selectinload(Estimate.employees))
        .where(Estimate.id == estimate_id)
    )
    est = result.scalar_one_or_none()
    if not est:
        raise HTTPException(404, "Estimate not found")

    # Update scalar fields
    for field in [
        "project_name", "start_date", "end_date", "working_days",
        "partner_pay_per_hour", "partner_cost", "team_cost", "grand_total",
        "project_color", "status",
    ]:
        val = getattr(data, field, None)
        if val is not None:
            setattr(est, field, val)

    # Replace employees if provided
    if data.employees is not None:
        est.employees.clear()
        for emp in data.employees:
            est.employees.append(
                EstimateEmployee(
                    emp_type=emp.emp_type,
                    base_pay=emp.base_pay,
                    hrs_per_day=emp.hrs_per_day,
                    pay_per_hour=emp.pay_per_hour,
                    total_hours=emp.total_hours,
                    total_cost=emp.total_cost,
                )
            )

    await db.commit()
    await db.refresh(est, attribute_names=["employees"])
    return serialize_estimate(est)


@router.delete("/{estimate_id}", status_code=204)
async def delete_estimate(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    result = await db.execute(
        select(Estimate).where(Estimate.id == estimate_id)
    )
    est = result.scalar_one_or_none()
    if not est:
        raise HTTPException(404, "Estimate not found")
    await db.delete(est)
    await db.commit()
