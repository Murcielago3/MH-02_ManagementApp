"""Compensatory ("comp-off") leave earned from overtime.

One row per (timesheet, work_date) that qualified: an 11h+ day earns 0.5 day and
a 13h+ day earns 1.0 day of paid leave, granted when the timesheet is fully
approved. Each credit is valid for 40 days from the *work date* (not the approval
date). Consumed automatically, soonest-expiry first, when a leave is approved.
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
    expires_on = Column(Date, nullable=False)      # work_date + 40 days
    created_at = Column(DateTime(timezone=True), server_default=func.now())
