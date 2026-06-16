from sqlalchemy import Column, Integer, String, Date, ForeignKey, Numeric, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class WeeklyTimesheet(Base):
    __tablename__ = 'weekly_timesheets'

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey('users.id'))
    week_start = Column(Date, nullable=False)
    week_end = Column(Date, nullable=False)
    total_hours = Column(Numeric(6, 2), nullable=True) # Changed to Numeric for decimal hours
    description = Column(String, nullable=True) # Keeping global description just in case, but can be optional
    status = Column(String, nullable=False)
    rejection_reason = Column(String, nullable=True)

    employee = relationship("User", foreign_keys=[employee_id], back_populates="weekly_timesheets")
    entries = relationship("WeeklyTimesheetEntry", back_populates="timesheet", cascade="all, delete-orphan")

class WeeklyTimesheetEntry(Base):
    __tablename__ = 'weekly_timesheet_entries'

    id = Column(Integer, primary_key=True)
    timesheet_id = Column(Integer, ForeignKey("weekly_timesheets.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    hours = Column(Numeric(5, 2), nullable=False)
    description = Column(String, nullable=True)
    # Per-day breakdown for the week, Mon..Sun, e.g. [8, 8, 8, 8, 8, 0, 0].
    # Null for entries submitted before this field existed.
    daily_hours = Column(JSON, nullable=True)

    timesheet = relationship("WeeklyTimesheet", back_populates="entries")
    project = relationship("Project", foreign_keys=[project_id])