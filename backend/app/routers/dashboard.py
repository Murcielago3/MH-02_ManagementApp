from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.auth import require_admin
from app.models.expense import Expense


router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    from datetime import datetime
    current_year = datetime.now().year

    # Total FY Turnover (current year)
    fy_turnover_result = await db.execute(
        select(func.sum(Project.project_remuneration)).where(Project.year == current_year)
    )
    total_fy_turnover = fy_turnover_result.scalar() or 0

    # Billed vs Unbilled (current year)
    billed_result = await db.execute(
        select(func.sum(Project.project_remuneration)).where(
            Project.is_billed == "billed",
            Project.year == current_year
        )
    )
    total_billed = billed_result.scalar() or 0
    unbilled_result = await db.execute(
        select(func.sum(Project.project_remuneration)).where(
            Project.is_billed == "unbilled",
            Project.year == current_year
        )
    )
    total_unbilled = unbilled_result.scalar() or 0

    # FY Expenses breakdown (independent values)
    salary_result = await db.execute(
        select(func.sum(User.salary_month)).where(User.is_active == True)
    )
    salary_expense = salary_result.scalar() or 0

    rent_result = await db.execute(
        select(func.sum(Expense.amount)).where(Expense.category == "rent")
    )
    office_rent = rent_result.scalar() or 0

    utilities_result = await db.execute(
        select(func.sum(Expense.amount)).where(Expense.category == "utilities")
    )
    electricity_bills = utilities_result.scalar() or 0

    software_result = await db.execute(
        select(func.sum(Expense.amount)).where(Expense.category == "software")
    )
    software_licenses = software_result.scalar() or 0

    misc_result = await db.execute(
        select(func.sum(Expense.amount)).where(Expense.category == "misc")
    )
    misc_expenses = misc_result.scalar() or 0

    total_fy_expenses = float(salary_expense) + float(office_rent) + float(electricity_bills) + float(software_licenses) + float(misc_expenses)

    # Monthly sales data
    monthly_sales = {
        "January": 0, "February": 0, "March": 0,
        "April": 0, "May": 0, "June": 0,
        "July": 0, "August": 0, "September": 0,
        "October": 0, "November": 0, "December": 0,
    }

    projects_result = await db.execute(
        select(Project).where(Project.year == current_year)
    )
    projects = projects_result.scalars().all()

    months = list(monthly_sales.keys())
    for idx, project in enumerate(projects):
        month_idx = idx % 12
        monthly_sales[months[month_idx]] += float(project.project_remuneration or 0)

    return {
        "total_fy_turnover": float(total_fy_turnover),
        "total_billed": float(total_billed),
        "total_unbilled": float(total_unbilled),
        "fy_expenses": {
            "salary": float(salary_expense),
            "office_rent": float(office_rent),
            "electricity_bills": float(electricity_bills),
            "software_licenses": float(software_licenses),
            "misc": float(misc_expenses),
            "total": total_fy_expenses
        },
        "monthly_sales": monthly_sales
    }