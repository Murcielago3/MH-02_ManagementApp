from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Reimbursement(Base):
    __tablename__ = "reimbursements"

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    reason = Column(String, nullable=False)
    date = Column(Date, nullable=False)          # expense date chosen by the employee
    proof_url = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, approved, rejected
    # Which salary-slip month this claim is bundled into once approved. Derived
    # from the expense date's month, so a June-dated bill rolls into June's slip —
    # which pays out the following month (~Jul 7).
    month_added = Column(String, nullable=True)  # e.g. "2026-06"
    # When the employee submitted the claim (recorded going forward).
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    employee = relationship("User", foreign_keys=[employee_id])