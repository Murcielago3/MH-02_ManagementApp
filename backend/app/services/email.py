"""SMTP email notifications for MH-02.

Mirrors ``app/services/slack.py``: one synchronous sender that every email flows
through, dispatched from FastAPI routes via ``BackgroundTasks`` so the request
is never blocked, and which **never raises** - an SMTP outage must not break an
employee applying for leave or submitting a timesheet.

Sends no-op (returning False, logged) when ``SMTP_HOST`` is unset, so the app
runs fine with email switched off.

Recipients: pass them in explicitly. Routes resolve them with
``admin_recipients(db)`` while they still have a DB session - the background
thread does no DB work.
"""
import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)


def _sender() -> str:
    return settings.SMTP_FROM or settings.SMTP_USER or "no-reply@studiomh02.com"


async def admin_recipients(db: AsyncSession) -> list[str]:
    """Who gets approval notifications: the MAIL_NOTIFY_TO override if set,
    otherwise every active admin's studio email. Approval is admin-only, so
    admins are the correct audience."""
    if settings.MAIL_NOTIFY_TO:
        return [e.strip() for e in settings.MAIL_NOTIFY_TO.split(",") if e.strip()]
    rows = (await db.execute(
        select(User.studio_email).where(
            User.is_active.is_(True),
            User.role == "admin",
            User.studio_email.isnot(None),
        )
    )).scalars().all()
    return [e for e in rows if e]


def send_email(subject: str, body: str, to: list[str], *, reply_to: str | None = None) -> bool:
    """Send a plain-text email. Returns True on success, False otherwise.

    Never raises - callers are user-facing actions that must succeed regardless.
    """
    if not settings.SMTP_HOST:
        logger.warning("SMTP_HOST not set - skipping email %r.", subject)
        return False
    recipients = [e for e in (to or []) if e]
    if not recipients:
        logger.warning("No recipients for email %r - skipping.", subject)
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((settings.SMTP_FROM_NAME, _sender()))
    msg["To"] = ", ".join(recipients)
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(body)

    try:
        if settings.SMTP_USE_SSL:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
        with server:
            server.ehlo()
            if settings.SMTP_USE_TLS and not settings.SMTP_USE_SSL:
                server.starttls()
                server.ehlo()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("Sent email %r to %s recipient(s).", subject, len(recipients))
        return True
    except Exception:
        # Bad credentials, blocked port, TLS mismatch, DNS - all non-fatal.
        logger.exception("Failed to send email %r.", subject)
        return False


# ─────────────────────────── message builders ───────────────────────────
# Kept here so wording lives next to the sender rather than in the routers.

def leave_applied_email(employee_name: str, start, end, days: int, reason: str | None):
    span = f"{start}" if start == end else f"{start} to {end}"
    subject = f"Leave request - {employee_name} ({span})"
    body = (
        f"{employee_name} has applied for leave.\n\n"
        f"Dates   : {span}\n"
        f"Working days: {days}\n"
        f"Reason  : {reason or '-'}\n\n"
        f"Review it in the admin portal under Leaves.\n"
    )
    return subject, body


def timesheet_submitted_email(employee_name: str, week_start, week_end, total_hours):
    subject = f"Timesheet submitted - {employee_name} (week of {week_start})"
    body = (
        f"{employee_name} has submitted a weekly timesheet.\n\n"
        f"Week  : {week_start} to {week_end}\n"
        f"Hours : {total_hours}\n\n"
        f"Review it in the admin portal under Timesheets.\n"
    )
    return subject, body
