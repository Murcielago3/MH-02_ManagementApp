"""Monthly salary slip.

One row per (employee, salary-month). Net pay is:
    net_total = base_salary - tds_amount + reimbursement_total

Slips are generated automatically (idempotent) for completed months and
approved by an admin before they are considered final. Reimbursements bundled
into a slip are the *approved* ones whose `month_added` matches the slip month.
"""
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class SalarySlip(Base):
    __tablename__ = "salary_slips"
    __table_args__ = (
        UniqueConstraint("employee_id", "month", name="uq_salary_slip_employee_month"),
    )

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Salary period as "YYYY-MM" (e.g. "2026-05")
    month = Column(String, nullable=False)

    base_salary = Column(Numeric(12, 2), nullable=False, default=0)
    tds_percent = Column(Numeric(5, 2), nullable=False, default=0)   # snapshot of rate used
    tds_amount = Column(Numeric(12, 2), nullable=False, default=0)
    reimbursement_total = Column(Numeric(12, 2), nullable=False, default=0)
    # Unpaid-leave salary cut for the month (hourly_rate * 8 * unpaid_days)
    paid_leave_days = Column(Numeric(5, 1), default=0)
    unpaid_leave_days = Column(Numeric(5, 1), default=0)
    leave_deduction = Column(Numeric(12, 2), default=0)
    net_total = Column(Numeric(12, 2), nullable=False, default=0)

    # Date the pay is scheduled to go out (7th of following month, Sunday-adjusted).
    payout_date = Column(Date, nullable=True)

    status = Column(String, default="pending")  # pending, approved

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)

    employee = relationship("User", foreign_keys=[employee_id])
