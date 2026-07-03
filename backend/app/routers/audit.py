"""Admin-only audit trail view."""
from typing import Optional
from datetime import date, datetime, time

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.audit_log import AuditLog
from app.auth import require_admin

router = APIRouter(prefix="/audit-logs", tags=["audit"])


def _ser(r: AuditLog) -> dict:
    return {
        "id": r.id,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "actor_id": r.actor_id,
        "actor_name": r.actor_name,
        "action": r.action,
        "entity_type": r.entity_type,
        "entity_id": r.entity_id,
        "summary": r.summary,
        "details": r.details,
    }


@router.get("/")
async def list_audit_logs(
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    actor_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin),
):
    conds = []
    if entity_type:
        conds.append(AuditLog.entity_type == entity_type)
    if action:
        conds.append(AuditLog.action == action)
    if actor_id:
        conds.append(AuditLog.actor_id == actor_id)
    if date_from:
        conds.append(AuditLog.created_at >= datetime.combine(date_from, time.min))
    if date_to:
        conds.append(AuditLog.created_at <= datetime.combine(date_to, time.max))

    total = (await db.execute(
        select(func.count(AuditLog.id)).where(*conds)
    )).scalar_one()

    rows = (await db.execute(
        select(AuditLog).where(*conds).order_by(desc(AuditLog.created_at)).limit(limit).offset(offset)
    )).scalars().all()

    return {"total": total, "items": [_ser(r) for r in rows]}


@router.get("/entity-types")
async def audit_entity_types(db: AsyncSession = Depends(get_db), current_user = Depends(require_admin)):
    rows = (await db.execute(
        select(AuditLog.entity_type).where(AuditLog.entity_type.isnot(None)).distinct()
    )).scalars().all()
    return sorted(rows)
