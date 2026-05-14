from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, Union
from pydantic import BaseModel, validator
from datetime import date
from app.database import get_db
from app.models.project import Project, ProjectAssignment
from app.models.user import User
from app.models.weekly_timesheet import WeeklyTimesheet, WeeklyTimesheetEntry
from app.auth import require_admin, require_manager
from sqlalchemy import text

router = APIRouter(prefix="/projects", tags=["projects"])

def parse_date(v):
    if not v:
        return None
    if isinstance(v, str):
        if v.strip() == "":
            return None
        return date.fromisoformat(v)
    return v

class ProjectCreate(BaseModel):
    project_number: str
    name: str
    location: Optional[str] = None
    gmap_link: Optional[str] = None
    year: Optional[int] = None
    current_stage: Optional[str] = None
    is_billed: str = "unbilled"
    client_id: Optional[int] = None
    partner_remuneration: Optional[float] = None
    employee_remuneration: Optional[float] = None
    project_remuneration: Optional[float] = None
    total_assigned_hours: Optional[float] = None
    color: Optional[str] = '#287475'
    employee_budget: Optional[float] = None
    partner_budget: Optional[float] = None
    partner_hourly_rate: Optional[float] = None
    start_date: Optional[Union[date, str]] = None
    end_date: Optional[Union[date, str]] = None

    @validator('start_date', 'end_date', pre=True)
    def parse_dates(cls, v):
        return parse_date(v)

class ProjectUpdate(BaseModel):
    project_number: Optional[str] = None
    name: Optional[str] = None
    location: Optional[str] = None
    gmap_link: Optional[str] = None
    year: Optional[int] = None
    current_stage: Optional[str] = None
    is_billed: Optional[str] = None
    client_id: Optional[int] = None
    partner_remuneration: Optional[float] = None
    employee_remuneration: Optional[float] = None
    project_remuneration: Optional[float] = None
    total_assigned_hours: Optional[float] = None
    color: Optional[str] = None
    employee_budget: Optional[float] = None
    partner_budget: Optional[float] = None
    partner_hourly_rate: Optional[float] = None
    start_date: Optional[Union[date, str]] = None
    end_date: Optional[Union[date, str]] = None

    @validator('start_date', 'end_date', pre=True)
    def parse_dates(cls, v):
        return parse_date(v)

class AssignmentUpdate(BaseModel):
    base_pay: Optional[float] = None
    hourly_rate: Optional[float] = None

@router.get("/next-number")
async def get_next_project_number(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    result = await db.execute(select(Project.project_number))
    numbers = result.scalars().all()
    
    max_num = 0
    for sn in numbers:
        if not sn: continue
        try:
            # Extract only digits from the whole string or after hyphen
            num_part = ''.join(filter(str.isdigit, sn))
            if num_part:
                max_num = max(max_num, int(num_part))
        except:
            continue
            
    next_num = max_num + 1
    return {"next_number": f"MH - {next_num:03d}"}

@router.get("/")
async def list_projects(
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    query = select(Project).options(selectinload(Project.client))
    if year:
        query = query.where(Project.year == year)
    result = await db.execute(query)
    projects = result.scalars().all()
    return projects 

@router.get("/{project_id}")
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    result = await db.execute(
        select(Project)
        .options(
            selectinload(Project.assignments).selectinload(ProjectAssignment.user),
            selectinload(Project.client)
        )
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    total_worked_hours = 0
    total_employee_cost = 0.0

    # Calculate for each assignment to get the correct cost
    assignments_data = []
    for assignment in project.assignments:
        worked_query = (
            select(func.sum(WeeklyTimesheetEntry.hours))
            .join(WeeklyTimesheet)
            .where(
                WeeklyTimesheetEntry.project_id == project_id,
                WeeklyTimesheet.employee_id == assignment.user_id,
                WeeklyTimesheet.status == 'approved'
            )
        )
        worked_result = await db.execute(worked_query)
        hours_worked = float(worked_result.scalar() or 0)
        hourly_rate = float(assignment.hourly_rate or 0)

        total_worked_hours += hours_worked
        total_employee_cost += (hours_worked * hourly_rate)
        
        # Build assignment dict with extra info
        assignments_data.append({
            "id": assignment.id,
            "user_id": assignment.user_id,
            "user": {
                "id": assignment.user.id,
                "name": assignment.user.name,
                "designation": assignment.user.designation
            },
            "base_pay": float(assignment.base_pay or 0),
            "hourly_rate": float(assignment.hourly_rate or 0),
            "hours_worked": hours_worked
        })
        
    partner_hourly_rate = float(project.partner_hourly_rate or 0)
    total_partner_cost = total_worked_hours * partner_hourly_rate
    
    # We can add this dynamically to the object or return a dict
    project_data = {
        "id": project.id,
        "project_number": project.project_number,
        "name": project.name,
        "location": project.location,
        "gmap_link": project.gmap_link,
        "year": project.year,
        "current_stage": project.current_stage,
        "is_billed": project.is_billed,
        "client_id": project.client_id,
        "start_date": project.start_date,
        "end_date": project.end_date,
        "employee_budget": float(project.employee_budget or 0),
        "partner_budget": float(project.partner_budget or 0),
        "partner_remuneration": float(total_partner_cost),
        "employee_remuneration": float(total_employee_cost),
        "project_remuneration": project.project_remuneration,
        "total_assigned_hours": project.total_assigned_hours,
        "total_worked_hours": float(total_worked_hours),
        "partner_hourly_rate": project.partner_hourly_rate,
        "color": project.color,
        "assignments": assignments_data,
        "work_order_urls": project.work_order_urls
    }
    return project_data

@router.post("/", status_code=201)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    # Check for duplicate project number
    existing_project = await db.execute(
        select(Project).where(Project.project_number == data.project_number)
    )
    if existing_project.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="A project with this project number already exists.")

    project = Project(
        project_number=data.project_number,
        name=data.name,
        location=data.location,
        gmap_link=data.gmap_link,
        year=data.year,
        current_stage=data.current_stage,
        is_billed=data.is_billed,
        client_id=data.client_id,
        start_date=data.start_date,
        end_date=data.end_date,
        employee_budget=data.employee_budget,
        partner_budget=data.partner_budget,
        partner_remuneration=data.partner_remuneration,
        employee_remuneration=data.employee_remuneration,
        project_remuneration=data.project_remuneration,
        total_assigned_hours=data.total_assigned_hours,
        color=data.color
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project

@router.patch("/{project_id}")
async def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    for field, value in data.dict(exclude_unset=True).items():
        setattr(project, field, value)
    
    await db.commit()
    await db.refresh(project)
    return project

@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    await db.commit()
    return {"detail": "Project deleted successfully"}

class AssignUserBody(BaseModel):
    user_id: int

class AssignEmployee(BaseModel):
    user_id: int
    base_pay: float

@router.post("/{project_id}/assign", status_code=201)
async def assign_employee(
    project_id:int,
    data: AssignEmployee,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    existing = await db.execute(
        select(ProjectAssignment).where(
            ProjectAssignment.project_id == project_id,
            ProjectAssignment.user_id == data.user_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Employee already assigned to this project")
    hourly_rate = round((data.base_pay * 13 / 12) / 160, 2)

    assignment = ProjectAssignment(
        user_id=data.user_id,
        project_id=project_id,
        base_pay=data.base_pay,
        hourly_rate=hourly_rate
    )
    db.add(assignment)
    await db.commit()
    return {
        "message": "Employee assigned",
        "user_id": data.user_id,
        "base_pay": data.base_pay,
        "hourly_rate": hourly_rate
    }

@router.patch("/{project_id}/assignments/{assignment_id}")
async def update_assignment(
    project_id: int,
    assignment_id: int,
    data: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    result = await db.execute(
        select(ProjectAssignment).where(
            ProjectAssignment.id == assignment_id,
            ProjectAssignment.project_id == project_id
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(404, "Assignment not found")
    
    if data.base_pay is not None:
        assignment.base_pay = data.base_pay
    if data.hourly_rate is not None:
        assignment.hourly_rate = data.hourly_rate
        
    await db.commit()
    await db.refresh(assignment)
    return assignment

@router.get("/{project_id}/summary")
async def get_project_summary(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    from sqlalchemy import func
    from app.models.weekly_timesheet import WeeklyTimesheet
    from app.models.user import User

    # Get project
    proj_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = proj_result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")

    # Get all assignments for this project
    assign_result = await db.execute(
        select(ProjectAssignment).where(
            ProjectAssignment.project_id == project_id
        )
    )
    assignments = assign_result.scalars().all()

    employee_rows = []
    total_hours_all = 0
    total_spent_all = 0

    for assignment in assignments:
        # Get employee name
        user_result = await db.execute(
            select(User).where(User.id == assignment.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            continue

        # Sum approved timesheet hours for this employee on this project
        # Using weekly_timesheet_entries table
        hours_result = await db.execute(
            text("""
                SELECT COALESCE(SUM(wte.hours), 0)
                FROM weekly_timesheet_entries wte
                JOIN weekly_timesheets wt ON wte.timesheet_id = wt.id
                WHERE wte.project_id = :project_id
                AND wt.employee_id = :employee_id
                AND wt.status = 'approved'
            """),
            {"project_id": project_id, "employee_id": assignment.user_id}
        )
        hours_worked = float(hours_result.scalar() or 0)
        hourly_rate = float(assignment.hourly_rate or 0)
        total_spent = round(hours_worked * hourly_rate, 2)

        total_hours_all += hours_worked
        total_spent_all += total_spent

        employee_rows.append({
            "employee_id": assignment.user_id,
            "name": user.name,
            "designation": user.designation,
            "base_pay": float(assignment.base_pay or 0),
            "hourly_rate": hourly_rate,
            "hours_worked": hours_worked,
            "total_spent": total_spent
        })

    # Partner remuneration
    partner_hourly_rate = float(project.partner_hourly_rate or 0)
    partner_cost = round(partner_hourly_rate * total_hours_all, 2)

    return {
        "project_id": project_id,
        "project_name": project.name,
        "employee_rows": employee_rows,
        "totals": {
            "total_hours": total_hours_all,
            "total_spent": total_spent_all,
            "type": "expense"
        },
        "partner": {
            "hourly_rate": partner_hourly_rate,
            "total_hours": total_hours_all,
            "partner_cost": partner_cost,
            "type": "profit"
        },
        "grand_total": total_spent_all + partner_cost
    }


@router.get("/{project_id}/billing")
async def get_project_billing(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    proj_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = proj_result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")

    # Get summary to calculate unbilled
    summary = await get_project_summary(project_id, db, current_user)
    total_cost = summary["totals"]["total_spent"] + summary["partner"]["partner_cost"]

    billed = float(project.billed_amount or 0)
    unbilled = max(0, total_cost - billed)

    return {
        "project_id": project_id,
        "project_name": project.name,
        "billed_amount": billed,
        "unbilled_amount": unbilled,
        "total_cost": total_cost,
        "pie_data": [
            {"label": "Billed", "value": billed},
            {"label": "Unbilled", "value": unbilled}
        ]
    }


@router.patch("/{project_id}/billing")
async def update_billing(
    project_id: int,
    billed_amount: float,
    partner_hourly_rate: float = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    proj_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = proj_result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")

    project.billed_amount = billed_amount
    if partner_hourly_rate is not None:
        project.partner_hourly_rate = partner_hourly_rate

    await db.commit()
    await db.refresh(project)
    return {"message": "Billing updated", "billed_amount": billed_amount}