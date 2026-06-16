from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, approved, rejected
    days_count = Column(Integer, nullable=False)
    # Working-day split computed at approval time
    paid_days = Column(Integer, default=0)
    unpaid_days = Column(Integer, default=0)

    employee = relationship("User", foreign_keys=[employee_id])


