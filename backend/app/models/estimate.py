from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Estimate(Base):
    __tablename__ = "estimates"

    id = Column(Integer, primary_key=True)
    project_name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    working_days = Column(Integer, default=0)
    partner_pay_per_hour = Column(Numeric(10, 2), default=0)
    partner_cost = Column(Numeric(12, 2), default=0)
    team_cost = Column(Numeric(12, 2), default=0)
    grand_total = Column(Numeric(12, 2), default=0)
    project_color = Column(String, default="#287475")
    status = Column(String, default="draft")  # draft, finalized
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employees = relationship("EstimateEmployee", back_populates="estimate", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])


class EstimateEmployee(Base):
    __tablename__ = "estimate_employees"

    id = Column(Integer, primary_key=True)
    estimate_id = Column(Integer, ForeignKey("estimates.id", ondelete="CASCADE"), nullable=False)
    emp_type = Column(String, nullable=False)  # Intern, Junior, Mid-Level, Senior, Employee
    base_pay = Column(Numeric(10, 2), nullable=False)
    hrs_per_day = Column(Numeric(4, 1), default=8)
    pay_per_hour = Column(Numeric(10, 2), default=0)
    total_hours = Column(Numeric(10, 2), default=0)
    total_cost = Column(Numeric(12, 2), default=0)

    estimate = relationship("Estimate", back_populates="employees")
