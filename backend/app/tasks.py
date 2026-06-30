"""Celery scheduled tasks — Slack reminders.

Celery runs these tasks synchronously, but the app's DB layer is async. Each
task opens its own short-lived event loop via ``asyncio.run()`` and uses a
dedicated engine with ``NullPool`` so DB connections are never cached against a
loop that ``asyncio.run()`` tears down between beat ticks (a classic asyncpg /
Celery gotcha that surfaces as "Future attached to a different loop").

Schedules live in ``app/celery_app.py`` (Celery Beat). To fire one on demand:

    celery -A app.celery_app call app.tasks.weekly_timesheet_reminder
"""
import asyncio
import logging
from datetime import date, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.pool import NullPool

from app.celery_app import celery_app
from app.config import settings
from app.services.slack import notify_event, lookup_user_id
from app.models.user import User
from app.models.weekly_timesheet import WeeklyTimesheet
from app.models.reimbursement import Reimbursement
from app.models.expense import Expense
from app.models.invoice import Invoice

logger = logging.getLogger(__name__)

# Dedicated engine for task use. NullPool => a fresh connection per run, so
# nothing is reused across the per-task event loops created by asyncio.run().
_task_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
_TaskSession = async_sessionmaker(bind=_task_engine, class_=AsyncSession, expire_on_commit=False)


def _rupees(value) -> str:
    return f"₹{float(value or 0):,.0f}"


# ─────────────────────────── Monthly admin report ───────────────────────────

@celery_app.task(name="app.tasks.monthly_admin_report")
def monthly_admin_report():
    """Post a previous-month summary to the management channel (1st @ 9am)."""
    return asyncio.run(_monthly_admin_report())


async def _monthly_admin_report() -> bool:
    today = date.today()
    first_this_month = today.replace(day=1)
    last_prev = first_this_month - timedelta(days=1)
    first_prev = last_prev.replace(day=1)
    label = first_prev.strftime("%B %Y")

    async with _TaskSession() as db:
        # Reimbursements raised in the month, grouped by status.
        reim_rows = (await db.execute(
            select(
                Reimbursement.status,
                func.count(Reimbursement.id),
                func.coalesce(func.sum(Reimbursement.amount), 0),
            )
            .where(Reimbursement.date >= first_prev, Reimbursement.date <= last_prev)
            .group_by(Reimbursement.status)
        )).all()
        reim_count = sum(r[1] for r in reim_rows)
        reim_total = sum(float(r[2]) for r in reim_rows)
        reim_by_status = {r[0]: (r[1], float(r[2])) for r in reim_rows}

        expense_total = (await db.execute(
            select(func.coalesce(func.sum(Expense.amount), 0))
            .where(Expense.date >= first_prev, Expense.date <= last_prev)
        )).scalar_one()

        inv_count, inv_total = (await db.execute(
            select(func.count(Invoice.id), func.coalesce(func.sum(Invoice.total), 0))
            .where(Invoice.invoice_date >= first_prev, Invoice.invoice_date <= last_prev)
        )).one()

        ts_count = (await db.execute(
            select(func.count(WeeklyTimesheet.id))
            .where(WeeklyTimesheet.week_start >= first_prev, WeeklyTimesheet.week_start <= last_prev)
        )).scalar_one()

        headcount = (await db.execute(
            select(func.count(User.id)).where(User.is_active.is_(True))
        )).scalar_one()

    pending = reim_by_status.get("pending", (0, 0.0))
    approved = reim_by_status.get("approved", (0, 0.0))

    summary = (
        f"*Reimbursements:* {reim_count} totalling {_rupees(reim_total)} "
        f"(pending {pending[0]} · {_rupees(pending[1])}, "
        f"approved {approved[0]} · {_rupees(approved[1])})\n"
        f"*Expenses logged:* {_rupees(expense_total)}\n"
        f"*Invoices raised:* {inv_count} totalling {_rupees(inv_total)}\n"
        f"*Timesheets submitted:* {ts_count}\n"
        f"*Active headcount:* {headcount}"
    )
    text = f"📊 Monthly report — {label}\n{summary}"
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": f"📊 Monthly report — {label}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": summary}},
    ]
    return notify_event("monthly_report", text, blocks)


# ─────────────────────────── Weekly timesheet nudge ──────────────────────────

@celery_app.task(name="app.tasks.weekly_timesheet_reminder")
def weekly_timesheet_reminder():
    """Nudge employees who haven't submitted this week's timesheet (Sun @ noon)."""
    return asyncio.run(_weekly_timesheet_reminder())


def _slack_tag(user) -> str:
    """An @mention for the user (resolved via email), or a bold name fallback.

    Tagging works once the bot has the ``users:read.email`` scope; until then it
    degrades to the plain name.
    """
    for email in (user.studio_email, user.personal_mail):
        uid = lookup_user_id(email)
        if uid:
            return f"<@{uid}>"
    return f"*{user.name}*"


def _collect_offenders(employees, submitted, weeks):
    """(user, [missing week_starts]) for each employee behind on a tracked week.

    Skips weeks before the employee joined. Pure function — no DB/network — so
    it's unit-testable.
    """
    offenders = []
    for u in employees:
        missing_weeks = [
            wk for wk in weeks
            if (u.id, wk) not in submitted
            and (u.joining_date is None or u.joining_date <= wk + timedelta(days=6))
        ]
        if missing_weeks:
            offenders.append((u, missing_weeks))
    return offenders


def _format_reminder(offenders, last_monday, this_monday) -> str:
    span = f"weeks of {last_monday.strftime('%d %b')} & {this_monday.strftime('%d %b %Y')}"

    def _which(missing_weeks):
        return " & ".join("last week" if wk == last_monday else "this week" for wk in missing_weeks)

    lines = "\n".join(f"• {_slack_tag(u)} — {_which(mw)}" for u, mw in offenders)
    return (
        f"⏰ *Timesheet reminder* — please submit your pending weekly timesheets "
        f"({span}):\n{lines}\n🙏"
    )


async def _weekly_timesheet_reminder() -> bool:
    today = date.today()
    this_monday = today - timedelta(days=today.weekday())   # Monday of this week
    last_monday = this_monday - timedelta(days=7)
    weeks = [last_monday, this_monday]                       # chronological

    async with _TaskSession() as db:
        employees = (await db.execute(
            select(User).where(User.is_active.is_(True), User.role == "employee")
        )).scalars().all()

        submitted = {
            (eid, ws) for eid, ws in (await db.execute(
                select(WeeklyTimesheet.employee_id, WeeklyTimesheet.week_start)
                .where(WeeklyTimesheet.week_start.in_(weeks))
            )).all()
        }

    offenders = _collect_offenders(employees, submitted, weeks)
    if not offenders:
        span = f"weeks of {last_monday.strftime('%d %b')} & {this_monday.strftime('%d %b %Y')}"
        return notify_event(
            "timesheet_reminder",
            f"✅ All timesheets are in for the {span}. Nice work, team!",
        )
    return notify_event("timesheet_reminder", _format_reminder(offenders, last_monday, this_monday))


# ─────────────────────── Promote scheduled salary raises ──────────────────────

@celery_app.task(name="app.tasks.promote_salary_periods")
def promote_salary_periods():
    """Flip the user's current-salary mirror to any period effective today
    (so future-dated raises become 'current' exactly on their date)."""
    return asyncio.run(_promote_salary_periods())


async def _promote_salary_periods() -> int:
    from app.models.salary_history import SalaryHistory
    today = date.today()
    updated = 0
    async with _TaskSession() as db:
        rows = (await db.execute(
            select(SalaryHistory).where(SalaryHistory.effective_from == today)
        )).scalars().all()
        for sh in rows:
            user = (await db.execute(select(User).where(User.id == sh.user_id))).scalar_one_or_none()
            if user:
                user.salary_month = sh.monthly_salary
                user.salary_hour = sh.salary_hour
                updated += 1
        await db.commit()
    return updated
