"""Append-only audit trail of major actions (admin-visible in Settings).

One row per significant event: who (actor), did what (action), to which entity,
when (created_at), with a human summary and optional structured details.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    actor_name = Column(String, nullable=True)          # denormalised so it survives user deletion

    action = Column(String, nullable=False, index=True)  # e.g. "timesheet.pm_approved"
    entity_type = Column(String, nullable=True, index=True)  # e.g. "timesheet"
    entity_id = Column(Integer, nullable=True)
    summary = Column(String, nullable=True)              # human-readable one-liner
    details = Column(JSON, nullable=True)
