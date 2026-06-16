from sqlalchemy import Column, Integer, Numeric, String, Date, Time, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Timesheet(Base):
    __tablename__ = "timesheets"

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    date = Column(Date, nullable=False)
    hours_logged = Column(Numeric(5, 2), nullable=False)
    notes = Column(String, nullable=True)

    employee = relationship("User", foreign_keys=[employee_id])
    project = relationship("Project", foreign_keys=[project_id])