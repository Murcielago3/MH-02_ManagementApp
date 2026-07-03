from fastapi import APIRouter, Depends, HTTPException, Response
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
from app.auth import require_admin, require_manager, require_employee
from sqlalchemy import text
from app.utils.cache import TTLCache

# Reserve-status is an org-wide aggregation (every project, every approved
# timesheet entry, every invoice). The ProjectSelector loads it on every page
# mount, so the same admin can trigger it many times in quick succession.
# Cache it briefly; mutating endpoints below (project, assignment, invoice
# creation) invalidate it explicitly.
_reserve_cache = TTLCache(ttl_seconds=15)
_RESERVE_KEY = "all"


def _invalidate_reserve():
    """Drop the reserve cache AND the dashboard cache — both are derived from
    the same underlying data (projects, invoices, timesheets, salaries)."""
    _reserve_cache.invalidate(_RESERVE_KEY)
    try:
        from app.routers.dashboard import _invalidate_dashboard
        _invalidate_dashboard()
    except Exception:
        pass  # dashboard module not yet imported on first call

from app.services.audit import log_audit

router = APIRouter(prefix="/projects", tags=["projects"])


def user_rates(user, salary_months_per_year: float = 13.0, working_hours_per_month: float = 160.0) -> tuple[float, float]:
    """
    Single source of truth for per-employee pay used across all project views
    (summary, totals, billing, projected cost). Salaries live on the User
    profile — assignments are pure many-to-many links and don't carry their
    own salary anymore (Estimates is the only place where per-row overrides
    are allowed, and that runs through its own store).

    The salary_months_per_year and working_hours_per_month parameters come from
    admin Settings (see settings router); callers should fetch them via
    get_or_create_settings() once per request. Defaults match the historical
    13/12/160 formula so this remains safe if no settings exist.

    Returns: (base_pay_monthly, hourly_rate)
      - base_pay = user.salary_month
      - hourly_rate = (base_pay * 13 / 12) / 160
    """
    if user is None:
        return 0.0, 0.0
    base_pay = float(user.salary_month or 0)
    if base_pay > 0:
        hourly_rate = round((base_pay * salary_months_per_year / 12) / working_hours_per_month, 2)
    else:
        hourly_rate = 0.0
    return base_pay, hourly_rate


async def _rate_params(db) -> tuple[float, float]:
    """Tiny helper: returns (salary_months_per_year, working_hours_per_month)
    from settings. Reads through the cached settings snapshot — invalidated
    automatically whenever an admin saves the Settings page."""
    from app.routers.settings import get_settings_snapshot
    s = await get_settings_snapshot(db)
    return (
        float(s["salary_months_per_year"] or 13),
        float(s["working_hours_per_month"] or 160),
    )


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
    # Alternate name printed on invoices instead of `name`. None/omitted =
    # "same as project name".
    display_name: Optional[str] = None
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
    advance_amount: Optional[float] = None
    start_date: Optional[Union[date, str]] = None
    end_date: Optional[Union[date, str]] = None

    @validator('start_date', 'end_date', pre=True)
    def parse_dates(cls, v):
        return parse_date(v)

class ProjectUpdate(BaseModel):
    project_number: Optional[str] = None
    name: Optional[str] = None
    display_name: Optional[str] = None
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
    advance_amount: Optional[float] = None
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

    from datetime import date as _date
    year_prefix = str(_date.today().year)[2:]  # e.g. "26" for 2026

    max_seq = 0
    for sn in numbers:
        if not sn:
            continue
        sn = sn.strip()
        # Match numbers in the new format: YY### (5 chars, starts with current year)
        if len(sn) == 5 and sn[:2] == year_prefix and sn[2:].isdigit():
            max_seq = max(max_seq, int(sn[2:]))

    return {"next_number": f"{year_prefix}{max_seq + 1:03d}"}


@router.get("/reserve-status")
async def get_reserve_status(
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    """
    Returns reserve balance for every project in a single optimised SQL query.
    Formula: advance_amount + SUM(invoices.subtotal) - employee_spend - partner_cost

    Employee hourly rate is computed live from user.salary_month using the
    admin-configurable settings (same source of truth as /summary). This keeps
    the sidebar's depleted-reserve badge consistent with the per-project views.
    Must be registered BEFORE /{project_id} routes to avoid path conflict.

    Result is cached for 15s and invalidated whenever projects, assignments,
    or invoices are created/updated/deleted. Browser also gets a short
    Cache-Control window so rapid back-and-forth navigation hits the cache.
    """
    response.headers["Cache-Control"] = "private, max-age=5"

    cached = _reserve_cache.get(_RESERVE_KEY)
    if cached is not None:
        return cached

    sql = text("""
        WITH inv_cte AS (
            SELECT project_id, COALESCE(SUM(subtotal), 0) AS total_invoiced
            FROM invoices
            WHERE project_id IS NOT NULL
            GROUP BY project_id
        ),
        emp_cte AS (
            SELECT wte.project_id,
                   COALESCE(SUM(wte.employee_cost), 0) AS emp_cost,
                   COALESCE(SUM(wte.hours), 0) AS total_hours
            FROM weekly_timesheet_entries wte
            JOIN weekly_timesheets wt ON wt.id = wte.timesheet_id AND wt.status = 'approved'
            GROUP BY wte.project_id
        )
        SELECT
            p.id AS project_id,
            COALESCE(inv.total_invoiced, 0) AS total_invoiced,
            COALESCE(ec.emp_cost, 0) AS emp_cost,
            COALESCE(ec.total_hours, 0) * COALESCE(p.partner_hourly_rate, 0) AS partner_cost,
            (
                COALESCE(inv.total_invoiced, 0)
                - COALESCE(ec.emp_cost, 0)
                - COALESCE(ec.total_hours, 0) * COALESCE(p.partner_hourly_rate, 0)
            ) AS reserve_balance
        FROM projects p
        LEFT JOIN inv_cte inv ON inv.project_id = p.id
        LEFT JOIN emp_cte ec ON ec.project_id = p.id
    """)
    result = await db.execute(sql)
    rows = result.fetchall()
    payload = [
        {
            "project_id": row.project_id,
            "total_invoiced": float(row.total_invoiced),
            "reserve_balance": round(float(row.reserve_balance), 2),
            "reserve_depleted": float(row.total_invoiced) > 0 and float(row.reserve_balance) < 0,
            "has_reserve": float(row.total_invoiced) > 0,
        }
        for row in rows
    ]
    _reserve_cache.set(_RESERVE_KEY, payload)
    return payload


@router.get("/")
async def list_projects(
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_employee)
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

    total_worked_hours = 0.0
    total_employee_cost = 0.0

    # ── Frozen cost + hours per employee (summed across rate periods) ──
    # One row per assignment here (this endpoint is the team roster); the
    # per-rate-period split lives in /summary. employee_remuneration is the
    # point-in-time frozen total.
    from collections import defaultdict
    from app.services.salary import current_period

    agg = defaultdict(lambda: {"hours": 0.0, "cost": 0.0})
    if project.assignments:
        uids = [a.user_id for a in project.assignments]
        rows_q = await db.execute(
            select(
                WeeklyTimesheet.employee_id,
                WeeklyTimesheetEntry.employee_cost,
                WeeklyTimesheetEntry.hours,
            )
            .join(WeeklyTimesheetEntry, WeeklyTimesheetEntry.timesheet_id == WeeklyTimesheet.id)
            .where(
                WeeklyTimesheetEntry.project_id == project_id,
                WeeklyTimesheet.status == 'approved',
                WeeklyTimesheet.employee_id.in_(uids),
            )
        )
        for uid, emp_cost, hours in rows_q.all():
            agg[uid]["hours"] += float(hours or 0)
            agg[uid]["cost"] += float(emp_cost or 0)

    assignments_data = []
    for assignment in project.assignments:
        uid = assignment.user_id
        hours_worked = round(agg[uid]["hours"], 2)
        cost = round(agg[uid]["cost"], 2)
        cur = await current_period(db, uid)
        cur_rate = float(cur.hourly_rate) if cur and cur.hourly_rate is not None else 0.0
        base_pay = float(cur.monthly_salary) if cur and cur.monthly_salary is not None else float(assignment.user.salary_month or 0)
        blended_rate = round(cost / hours_worked, 2) if hours_worked > 0 else cur_rate

        total_worked_hours += hours_worked
        total_employee_cost += cost

        assignments_data.append({
            "id": assignment.id,
            "user_id": uid,
            "user": {
                "id": assignment.user.id,
                "name": assignment.user.name,
                "designation": assignment.user.designation,
            },
            "base_pay": base_pay,
            "hourly_rate": blended_rate,
            "hours_worked": hours_worked,
            "cost": cost,
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
        "work_order_urls": project.work_order_urls,
        "advance_amount": float(project.advance_amount or 0),
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
        display_name=data.display_name,
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
        color=data.color,
        advance_amount=data.advance_amount or 0,
    )
    db.add(project)
    await db.flush()
    await log_audit(db, current_user, "project.created", "project", project.id,
                    summary=f"Created project {project.project_number} — {project.name}")
    await db.commit()
    await db.refresh(project)
    _invalidate_reserve()
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

    # Pydantic v2: prefer model_dump over the deprecated .dict()
    payload = data.model_dump(exclude_unset=True)

    # If project_number is being changed, enforce the uniqueness check
    # ourselves so we return a clean 400 instead of letting Postgres raise
    # an IntegrityError that bubbles up as a 500 with no CORS headers.
    new_number = payload.get("project_number")
    if new_number and new_number != project.project_number:
        dupe = await db.execute(
            select(Project).where(
                Project.project_number == new_number,
                Project.id != project_id,
            )
        )
        if dupe.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="A project with this project number already exists.")

    try:
        for field, value in payload.items():
            setattr(project, field, value)
        await db.commit()
        await db.refresh(project)
    except Exception as e:
        await db.rollback()
        import logging, traceback
        logging.error("update_project failed for id=%s: %s\n%s", project_id, e, traceback.format_exc())
        raise HTTPException(status_code=400, detail=f"Failed to update project: {e}")

    _invalidate_reserve()
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
    await log_audit(db, current_user, "project.deleted", "project", project.id,
                    summary=f"Deleted project {project.project_number} — {project.name}")
    await db.delete(project)
    await db.commit()
    _invalidate_reserve()
    return {"detail": "Project deleted successfully"}

class AssignUserBody(BaseModel):
    user_id: int

class AssignEmployee(BaseModel):
    user_id: int
    # base_pay accepted for backward compat but ignored — salary is pulled from
    # the User profile (single source of truth).
    base_pay: Optional[float] = None

@router.post("/{project_id}/assign", status_code=201)
async def assign_employee(
    project_id: int,
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

    user_result = await db.execute(select(User).where(User.id == data.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "Employee not found")

    smpy, whpm = await _rate_params(db)
    base_pay, hourly_rate = user_rates(user, smpy, whpm)
    # We still snapshot these on the assignment row so older queries / DB
    # inspections see the values that were live at assignment time, but every
    # read path now recomputes from the user profile via user_rates().
    assignment = ProjectAssignment(
        user_id=data.user_id,
        project_id=project_id,
        base_pay=base_pay,
        hourly_rate=hourly_rate,
    )
    db.add(assignment)
    await db.commit()
    _invalidate_reserve()
    return {
        "message": "Employee assigned",
        "user_id": data.user_id,
        "base_pay": base_pay,
        "hourly_rate": hourly_rate,
    }

# Per-assignment salary override removed — salaries live on the User profile.
# Estimates remain the only place where per-row manipulation is supported.

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

    # ── Frozen per-entry cost grouped by (employee, salary period) ──
    # One row per (person × rate period): a raise mid-project shows as separate
    # rows, each priced at the rate that was in effect then.
    from collections import defaultdict
    from app.models.salary_history import SalaryHistory
    from app.services.salary import current_period

    rows_q = await db.execute(
        select(
            WeeklyTimesheet.employee_id,
            WeeklyTimesheetEntry.employee_cost,
            WeeklyTimesheetEntry.cost_breakdown,
            WeeklyTimesheetEntry.hours,
        )
        .join(WeeklyTimesheetEntry, WeeklyTimesheetEntry.timesheet_id == WeeklyTimesheet.id)
        .where(
            WeeklyTimesheetEntry.project_id == project_id,
            WeeklyTimesheet.status == "approved",
        )
    )
    buckets = defaultdict(lambda: {"hours": 0.0, "cost": 0.0, "rate": 0.0})
    hours_by_uid = defaultdict(float)
    for uid, emp_cost, breakdown, hours in rows_q.all():
        if breakdown:
            for b in breakdown:
                key = (uid, b.get("salary_history_id"))
                buckets[key]["hours"] += float(b.get("hours") or 0)
                buckets[key]["cost"] += float(b.get("cost") or 0)
                buckets[key]["rate"] = float(b.get("rate") or 0)
                hours_by_uid[uid] += float(b.get("hours") or 0)
        else:
            buckets[(uid, None)]["hours"] += float(hours or 0)
            buckets[(uid, None)]["cost"] += float(emp_cost or 0)
            hours_by_uid[uid] += float(hours or 0)

    # Also include formally assigned employees (they may have 0 hours so far)
    assign_result = await db.execute(
        select(ProjectAssignment).where(ProjectAssignment.project_id == project_id)
    )
    assignments = assign_result.scalars().all()
    assigned_user_ids = {a.user_id for a in assignments}
    assignment_id_by_uid = {a.user_id: a.id for a in assignments}

    all_user_ids = list(set(hours_by_uid.keys()) | assigned_user_ids)

    users_by_id = {}
    if all_user_ids:
        users_result = await db.execute(select(User).where(User.id.in_(all_user_ids)))
        users_by_id = {u.id: u for u in users_result.scalars().all()}

    sh_ids = {sid for (_u, sid) in buckets if sid}
    sh_meta = {}
    if sh_ids:
        sh_rows = await db.execute(
            select(SalaryHistory.id, SalaryHistory.effective_from, SalaryHistory.monthly_salary)
            .where(SalaryHistory.id.in_(sh_ids))
        )
        sh_meta = {
            r[0]: {"from": str(r[1]), "monthly": float(r[2]) if r[2] is not None else None}
            for r in sh_rows.all()
        }

    employee_rows = []
    total_hours_all = 0.0
    total_spent_all = 0.0

    for uid in all_user_ids:
        user = users_by_id.get(uid)
        if not user:
            continue
        user_buckets = sorted(
            [(sid, v) for (u, sid), v in buckets.items() if u == uid],
            key=lambda x: sh_meta.get(x[0], {}).get("from", ""),
        )
        if not user_buckets:
            cur = await current_period(db, uid)
            employee_rows.append({
                "assignment_id": assignment_id_by_uid.get(uid),
                "employee_id": uid, "name": user.name, "designation": user.designation,
                "base_pay": float(cur.monthly_salary) if cur and cur.monthly_salary is not None else float(user.salary_month or 0),
                "hourly_rate": float(cur.hourly_rate) if cur and cur.hourly_rate is not None else 0.0,
                "hours_worked": 0.0, "total_spent": 0.0, "effective_from": None,
            })
            continue
        for sid, v in user_buckets:
            total_hours_all += v["hours"]
            total_spent_all += v["cost"]
            meta = sh_meta.get(sid, {})
            employee_rows.append({
                "assignment_id": assignment_id_by_uid.get(uid),
                "employee_id": uid, "name": user.name, "designation": user.designation,
                "base_pay": meta.get("monthly") if meta.get("monthly") is not None else float(user.salary_month or 0),
                "hourly_rate": round(v["rate"], 2),
                "hours_worked": round(v["hours"], 2),
                "total_spent": round(v["cost"], 2),
                "effective_from": meta.get("from"),
            })

    # Partner remuneration
    partner_hourly_rate = float(project.partner_hourly_rate or 0)
    partner_cost = round(partner_hourly_rate * total_hours_all, 2)
    grand_total = total_spent_all + partner_cost

    # Reserve balance: invoices billed to this project - actual spend
    from app.models.invoice import Invoice
    inv_result = await db.execute(
        select(func.coalesce(func.sum(Invoice.subtotal), 0))
        .where(Invoice.project_id == project_id)
    )
    total_invoiced = float(inv_result.scalar() or 0)
    reserve_balance = round(total_invoiced - grand_total, 2)
    has_reserve = total_invoiced > 0

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
        "grand_total": grand_total,
        "total_invoiced": total_invoiced,
        "reserve_balance": reserve_balance,
        "reserve_depleted": has_reserve and reserve_balance < 0,
        "has_reserve": has_reserve,
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
    _invalidate_reserve()  # partner_hourly_rate affects partner_cost in reserve
    return {"message": "Billing updated", "billed_amount": billed_amount}


@router.get("/{project_id}/projected-cost")
async def get_projected_cost(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_manager)
):
    """
    Calculates projected cost based on tasks scheduled for this project.
    Uses duration_hours when set, otherwise (end_date - date + 1) * 8 hours.
    Includes all task statuses.
    """
    from app.models.task import Task

    # Get project for partner rate
    proj_result = await db.execute(select(Project).where(Project.id == project_id))
    project = proj_result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")

    partner_hourly_rate = float(project.partner_hourly_rate or 0)

    # Get all tasks for this project
    tasks_result = await db.execute(
        select(Task).where(Task.project_id == project_id)
    )
    tasks = tasks_result.scalars().all()

    # Get user ids from tasks
    task_user_ids = list(set([t.assigned_to for t in tasks]))

    # Fetch approved leaves
    from app.models.leave import LeaveRequest
    user_leaves = {}
    if task_user_ids:
        leaves_result = await db.execute(
            select(LeaveRequest).where(
                LeaveRequest.employee_id.in_(task_user_ids),
                LeaveRequest.status == 'approved'
            )
        )
        all_leaves = leaves_result.scalars().all()
        for l in all_leaves:
            user_leaves.setdefault(l.employee_id, []).append((l.start_date, l.end_date))

    import datetime
    def count_working_days(uid, start, end):
        days = (end - start).days + 1
        leaves = user_leaves.get(uid, [])
        overlap_days = 0
        for i in range(days):
            current = start + datetime.timedelta(days=i)
            for l_start, l_end in leaves:
                if l_start <= current <= l_end:
                    overlap_days += 1
                    break
        return max(days - overlap_days, 0)

    from datetime import date as date_type
    emp_hours: dict = {}
    for task in tasks:
        uid = task.assigned_to
        task_end = task.end_date or task.date
        working_days = count_working_days(uid, task.date, task_end)
        
        if working_days == 0:
            hours = 0.0
        else:
            hrs_per_day = float(task.duration_hours) if task.duration_hours is not None else 8.0
            hours = working_days * hrs_per_day
            
        emp_hours[uid] = emp_hours.get(uid, 0) + hours

    if not emp_hours:
        return {
            "project_id": project_id,
            "rows": [],
            "total_employee_projected": 0,
            "total_projected_hours": 0,
            "partner_projected_cost": 0,
            "grand_projected": 0,
        }

    # Fetch users — salary is the single source of truth (no assignment override)
    from app.models.user import User
    user_ids = list(emp_hours.keys())
    users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users = {u.id: u for u in users_result.scalars().all()}

    smpy, whpm = await _rate_params(db)
    rows = []
    total_emp_projected = 0.0
    total_proj_hours = 0.0

    for uid, proj_hours in emp_hours.items():
        user = users.get(uid)
        name = user.name if user else f"Employee #{uid}"
        designation = (user.designation if user else None) or "—"
        _, hourly_rate = user_rates(user, smpy, whpm)

        projected_cost = round(proj_hours * hourly_rate, 2)
        total_emp_projected += projected_cost
        total_proj_hours += proj_hours

        rows.append({
            "employee_id": uid,
            "name": name,
            "designation": designation,
            "projected_hours": round(proj_hours, 1),
            "hourly_rate": hourly_rate,
            "projected_cost": projected_cost,
        })

    rows.sort(key=lambda r: r["name"])
    partner_projected = round(total_proj_hours * partner_hourly_rate, 2)
    grand_projected = round(total_emp_projected + partner_projected, 2)

    return {
        "project_id": project_id,
        "rows": rows,
        "total_employee_projected": round(total_emp_projected, 2),
        "total_projected_hours": round(total_proj_hours, 1),
        "partner_projected_cost": partner_projected,
        "grand_projected": grand_projected,
    }