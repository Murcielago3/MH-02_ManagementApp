from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Numeric
from sqlalchemy.sql import func
from app.database import Base


class Subtask(Base):
    __tablename__ = "subtasks"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    duration_hours = Column(Numeric(6, 2), nullable=True)  # legacy — superseded by due_date
    # A subtask runs from the day it was assigned to its deadline.
    start_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    status = Column(String, default="pending")  # pending, in-progress, completed
    # Transition stamps — the basis for quarterly on-time / never-started stats.
    # Null on rows that predate this, which the report reports as "unknown"
    # rather than guessing.
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
