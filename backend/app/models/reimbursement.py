from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Reimbursement(Base):
    __tablename__ = "reimbursements"

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    reason = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    proof_url = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, approved, rejected
    month_added = Column(String, nullable=True)  # e.g. "2026-06" when added to payroll

    employee = relationship("User", foreign_keys=[employee_id])