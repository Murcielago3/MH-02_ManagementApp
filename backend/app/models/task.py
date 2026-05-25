from sqlalchemy import Column, Integer, String, Date, ForeignKey
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

    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    project = relationship("Project", foreign_keys=[project_id])
    assignee = relationship("User", foreign_keys=[assigned_to])
    assigner = relationship("User", foreign_keys=[assigned_by])