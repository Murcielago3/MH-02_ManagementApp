"""
Admin dashboard stats.

Uses the same reserve/invoice math as /projects/reserve-status and the project
reports view, just aggregated org-wide instead of per-project.
"""
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime, date

from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.invoice import Invoice
from app.models.expense import Expense
from app.auth import require_manager
from app.utils.cache import TTLCache


router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Dashboard is one of the most-loaded pages; everyone hits it on login.
# Org-wide aggregations are expensive — cache for 30s, invalidate on the
# usual mutation points (we piggyback on _invalidate_reserve from projects).
_dashboard_cache = TTLCache(ttl_seconds=30)
_DASH_KEY = "stats"


def _invalidate_dashboard():
    _dashboard_cache.invalidate(_DASH_KEY)


@router.get("/stats")
async def get_dashboard_stats(
    response: Response,
    current_user: User = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
):
    response.headers["Cache-Control"] = "private, max-age=10"
    cached = _dashboard_cache.get(_DASH_KEY)
    if cached is not None:
        return cached

    current_year = datetime.now().year

    # ── Org-wide reserve / billing aggregation (frozen per-entry costs) ──
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
    rows = (await db.execute(sql)).fetchall()

    total_invoiced = 0.0
    total_employee_remuneration = 0.0
    total_partner_remuneration = 0.0
    total_profit = 0.0
    total_unbilled = 0.0

    for r in rows:
        invoiced = float(r.total_invoiced)
        emp = float(r.emp_cost)
        partner = float(r.partner_cost)
        reserve = float(r.reserve_balance)
        total_invoiced += invoiced
        total_employee_remuneration += emp
        total_partner_remuneration += partner
        if reserve > 0:
            total_profit += reserve
        elif reserve < 0 and invoiced > 0:
            total_unbilled += -reserve

    total_billed = round(total_invoiced, 2)
    total_unbilled = round(total_unbilled, 2)
    total_profit = round(total_profit, 2)
    total_employee_remuneration = round(total_employee_remuneration, 2)
    total_partner_remuneration = round(total_partner_remuneration, 2)

    # ── Total turnover for the current calendar year (invoices only) ──
    fy_inv_result = await db.execute(
        select(func.coalesce(func.sum(Invoice.subtotal), 0))
        .where(func.extract('year', Invoice.invoice_date) == current_year)
    )
    total_fy_turnover = round(float(fy_inv_result.scalar() or 0), 2)

    # ── Trailing-12-month sales (invoice subtotals bucketed by month) ──
    # Window is `today - 1 year` → `today`, which spans 13 calendar months;
    # the first and last buckets are partial. Returned as an ordered list so
    # the frontend doesn't need to know about year wrap.
    today = date.today()
    try:
        start_date = today.replace(year=today.year - 1)
    except ValueError:
        # Today is Feb 29 of a leap year; step the start to Feb 28.
        start_date = today.replace(year=today.year - 1, day=28)

    buckets: list[tuple[int, int]] = []
    y, m = start_date.year, start_date.month
    while (y, m) <= (today.year, today.month):
        buckets.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)

    sales_by_ym: dict[tuple[int, int], float] = {ym: 0.0 for ym in buckets}
    monthly_q = await db.execute(
        select(
            func.extract('year', Invoice.invoice_date).label('y'),
            func.extract('month', Invoice.invoice_date).label('m'),
            func.coalesce(func.sum(Invoice.subtotal), 0).label('s'),
        )
        .where(Invoice.invoice_date >= start_date, Invoice.invoice_date <= today)
        .group_by('y', 'm')
    )
    for row in monthly_q:
        key = (int(row.y), int(row.m))
        if key in sales_by_ym:
            sales_by_ym[key] = float(row.s or 0)

    monthly_sales = [
        {"label": date(yy, mm, 1).strftime("%b '%y"), "revenue": sales_by_ym[(yy, mm)]}
        for (yy, mm) in buckets
    ]

    current_month = datetime.now().month

    # ── Current-month expense categories ──
    async def _sum_exp_month(cat):
        r = await db.execute(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(
                Expense.category == cat,
                func.extract('year', Expense.date) == current_year,
                func.extract('month', Expense.date) == current_month,
            )
        )
        return float(r.scalar() or 0)

    office_rent = await _sum_exp_month("rent")
    electricity_bills = await _sum_exp_month("utilities")
    software_licenses = await _sum_exp_month("software")
    misc_expenses = await _sum_exp_month("misc")

    # Monthly payroll = sum of active employee salaries (current snapshot)
    salary_q = await db.execute(
        select(func.coalesce(func.sum(User.salary_month), 0)).where(User.is_active == True)
    )
    monthly_payroll = round(float(salary_q.scalar() or 0), 2)

    current_month_expenses = round(
        monthly_payroll + office_rent + electricity_bills + software_licenses + misc_expenses, 2
    )

    payload = {
        "total_fy_turnover": total_fy_turnover,
        "total_billed": total_billed,
        "total_unbilled": total_unbilled,
        "total_profit": total_profit,
        "total_employee_remuneration": total_employee_remuneration,
        "total_partner_remuneration": total_partner_remuneration,
        "monthly_payroll": monthly_payroll,
        "fy_expenses": {
            "salary": monthly_payroll,
            "office_rent": round(office_rent, 2),
            "electricity_bills": round(electricity_bills, 2),
            "software_licenses": round(software_licenses, 2),
            "misc": round(misc_expenses, 2),
            "total": current_month_expenses,
        },
        "monthly_sales": monthly_sales,
    }
    _dashboard_cache.set(_DASH_KEY, payload)
    return payload
