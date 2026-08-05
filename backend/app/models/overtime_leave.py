"""Compensatory ("comp-off") leave earned from overtime.

One row per (timesheet, work_date) that qualified. Weekdays: a 12h+ day earns
0.5, a 14h+ day earns 1.0. Saturday: any work earns comp - 8h+ = 1.0, under 8h
= 0.5 (Sunday is no-work). Paid-leave credit is granted when the timesheet is fully
approved. Comp-off credits do NOT expire — a credit stays usable until it's
consumed. Consumed automatically, oldest-earned first, when a leave is approved.
"""
from sqlalchemy import Column, Integer, Numeric, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class OvertimeLeave(Base):
    __tablename__ = "overtime_leaves"
    __table_args__ = (
        UniqueConstraint("timesheet_id", "work_date", name="uq_overtime_ts_day"),
    )

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # The timesheet whose approval granted this credit (revoked if it's rejected).
    timesheet_id = Column(Integer, ForeignKey("weekly_timesheets.id", ondelete="CASCADE"), nullable=True)
    work_date = Column(Date, nullable=False)      # the overtime day
    hours = Column(Numeric(6, 2), nullable=False)  # hours logged that day
    amount = Column(Numeric(3, 1), nullable=False)  # 0.5 or 1.0 days earned
    consumed = Column(Numeric(3, 1), nullable=False, default=0)  # days already used
    expires_on = Column(Date, nullable=False)      # legacy: retained NOT NULL, no longer enforced
    created_at = Column(DateTime(timezone=True), server_default=func.now())
