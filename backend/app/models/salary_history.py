"""Effective-dated salary history.

One row per rate period for an employee / project_manager. The salary in effect
on a date D is the row with the greatest ``effective_from <= D`` (with the
earliest row acting as a floor for any earlier date). ``effective_to`` is a
derived convenience (``next.effective_from - 1 day``); the latest row's
``effective_to`` is NULL = open until the next raise or exit.

Each row freezes the inputs *and* the resulting hourly rate, so historical pay
is immutable even if global Settings (smpy/whpm) change later — that's the point
of versioning.
"""
from sqlalchemy import (
    Column, Integer, String, Date, Numeric, ForeignKey, DateTime, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from app.database import Base


class SalaryHistory(Base):
    __tablename__ = "salary_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    monthly_salary = Column(Numeric(10, 2), nullable=True)
    salary_hour = Column(Numeric(8, 2), nullable=True)       # explicit override; bypasses the formula
    smpy = Column(Numeric(4, 2), nullable=True)              # salary_months_per_year snapshot
    whpm = Column(Numeric(6, 2), nullable=True)              # working_hours_per_month snapshot
    hourly_rate = Column(Numeric(10, 2), nullable=True)      # frozen computed rate for this period

    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)               # derived = next.effective_from - 1; NULL = open
    note = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        UniqueConstraint("user_id", "effective_from", name="uq_salary_user_effrom"),
    )
