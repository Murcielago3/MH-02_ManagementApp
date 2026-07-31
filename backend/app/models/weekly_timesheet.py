from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Numeric, JSON
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
    # Approval slots. A non-admin timesheet is fully approved ('approved') only
    # when BOTH admin slots are filled — the two admins must be different
    # accounts (four-eyes). An admin's own timesheet needs only the single admin
    # slot. Only admins approve or reject.
    status = Column(String, nullable=False)  # submitted, admin_approved, approved, rejected
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    # Deprecated: project managers no longer approve timesheets. Retained so the
    # historical record (and CSV exports) of past PM approvals stays intact.
    pm_approved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    pm_approved_at = Column(DateTime(timezone=True), nullable=True)
    admin_approved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    admin_approved_at = Column(DateTime(timezone=True), nullable=True)
    # Second admin approval (the "second factor"); required for non-admin timesheets.
    admin2_approved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    admin2_approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(String, nullable=True)

    employee = relationship("User", foreign_keys=[employee_id], back_populates="weekly_timesheets")
    entries = relationship("WeeklyTimesheetEntry", back_populates="timesheet", cascade="all, delete-orphan")

class WeeklyTimesheetEntry(Base):
    __tablename__ = 'weekly_timesheet_entries'

    id = Column(Integer, primary_key=True)
    timesheet_id = Column(Integer, ForeignKey("weekly_timesheets.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    # What the hours were spent on, when the project uses stages. Both optional:
    # projects without stages (and every pre-existing entry) leave them NULL.
    stage_id = Column(Integer, ForeignKey("project_stages.id", ondelete="SET NULL"), nullable=True)
    subtask_id = Column(Integer, ForeignKey("stage_subtasks.id", ondelete="SET NULL"), nullable=True)
    hours = Column(Numeric(5, 2), nullable=False)
    description = Column(String, nullable=True)
    # Per-day breakdown for the week, Mon..Sun, e.g. [8, 8, 8, 8, 8, 0, 0].
    # Null for entries submitted before this field existed.
    daily_hours = Column(JSON, nullable=True)
    # Frozen employee cost for this entry, set at approval from the salary
    # period(s) covering its days (see app/services/salary.py). Reserve/dashboard
    # sum this instead of recomputing from the current salary.
    employee_cost = Column(Numeric(12, 2), nullable=True)
    # Per-rate-period breakdown: [{salary_history_id, hours, rate, cost}, ...].
    # Usually one bucket; two when the week straddles a raise.
    cost_breakdown = Column(JSON, nullable=True)

    timesheet = relationship("WeeklyTimesheet", back_populates="entries")
    project = relationship("Project", foreign_keys=[project_id])