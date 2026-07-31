from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # if None, task is single day
    duration_hours = Column(Integer, nullable=True)  # e.g. 4 hours
    priority = Column(String, default="medium") # low, medium, high
    status = Column(String, default="pending")  # pending, in-progress, completed
    # Transition stamps for quarterly on-time / never-started stats.
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    # Which stage of the project this task band belongs to. Lets an admin create
    # stage subtasks straight from the tasks calendar.
    stage_id = Column(Integer, ForeignKey("project_stages.id", ondelete="SET NULL"), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    project = relationship("Project", foreign_keys=[project_id])
    assignee = relationship("User", foreign_keys=[assigned_to])
    assigner = relationship("User", foreign_keys=[assigned_by])