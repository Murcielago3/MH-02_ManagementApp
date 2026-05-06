from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.auth import require_admin

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    #total active employees
    emp_result = await db.execute(select(func.count(User.id)).select_from(User).where(User.is_active == True, User.role != "admin"))
    total_employees = emp_result.scalar()

    #total projects
    proj_result = await db.execute(select(func.count(Project.id)).select_from(Project))
    total_projects = proj_result.scalar()

    #billed vs unbilled amount till date
    billed_result = await db.execute(select(func.sum(Project.project_remuneration)).where(Project.is_billed == "billed"))
    total_billed = billed_result.scalar() or 0
    unbilled_result = await db.execute(select(func.sum(Project.project_remuneration)).where(Project.is_billed == "unbilled"))
    total_unbilled = unbilled_result.scalar() or 0

    #total expenditure till date (sum of all project budgets)
        # total salary expenditure
    salary_result = await db.execute(
        select(func.sum(User.salary_month)).where(User.is_active == True)
    )
    total_salary = salary_result.scalar() or 0

        # total partner remuneration across all projects
    partner_result = await db.execute(
        select(func.sum(Project.partner_remuneration))
    )
    total_partner = partner_result.scalar() or 0

    return {
        "total_employees": total_employees,
        "total_projects": total_projects,
        "total_billed": total_billed,
        "total_unbilled": total_unbilled,
        "monthly_salary_expenditure": float(total_salary),
        "total_partner_remuneration": float(total_partner),
        "total_expenditure": float(total_salary) + float(total_partner)
    }