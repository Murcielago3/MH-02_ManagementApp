from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from app.database import Base


class Subtask(Base):
    __tablename__ = "subtasks"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    duration_hours = Column(Numeric(6, 2), nullable=True)
    status = Column(String, default="pending")  # pending, in-progress, completed
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
