"""Audit-trail helper.

Call `log_audit(...)` from any endpoint after a meaningful action. It adds a row
to the *current request's* session — the caller's existing `commit()` persists it
atomically with the action. Logging never raises, so it can't break the action.
"""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


async def log_audit(
    db: AsyncSession,
    actor,
    action: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    summary: str | None = None,
    details: dict | None = None,
):
    """Queue an audit row on the session. Caller commits. Best-effort."""
    try:
        db.add(AuditLog(
            actor_id=getattr(actor, "id", None),
            actor_name=getattr(actor, "name", None),
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            summary=summary,
            details=details,
        ))
    except Exception:
        logger.exception("audit log failed for action=%s", action)
