"""Project stages and their subtasks.

A project's agreed value (``project_remuneration``) is split as:

    bucket = project_remuneration - advance_amount

Each stage claims a ``percentage`` of that bucket for invoicing, and the same
percentage of the project's ``total_assigned_hours`` as its time budget. Money
and hours are **derived, never stored** - if the project value or hour budget is
corrected later, every stage stays consistent automatically.

Stage subtasks are deliberately a separate table from ``subtasks`` (which is a
checklist inside a calendar Task). These are project-scoped: visible to the
whole studio, selectable on a timesheet, and completed by an admin or PM.
"""
from sqlalchemy import (
    Column, Integer, String, Date, DateTime, ForeignKey, Numeric, Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ProjectStage(Base):
    __tablename__ = "project_stages"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    # Display order within the project (0-based, assigned on create).
    sequence = Column(Integer, nullable=False, default=0)
    # Share of the post-advance bucket, e.g. 10.00 = 10%.
    percentage = Column(Numeric(6, 2), nullable=False, default=0)
    status = Column(String, nullable=False, default="active")  # active | completed

    completed_at = Column(DateTime, nullable=True)
    completed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    # Role of the creator, snapshotted so the stage header can show it even if
    # the person's role later changes.
    created_by_role = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    subtasks = relationship(
        "StageSubtask", back_populates="stage",
        cascade="all, delete-orphan", order_by="StageSubtask.id",
    )


class StageSubtask(Base):
    __tablename__ = "stage_subtasks"

    id = Column(Integer, primary_key=True)
    stage_id = Column(Integer, ForeignKey("project_stages.id", ondelete="CASCADE"), nullable=False)
    # Denormalised so "all subtasks on this project" is one cheap query and a
    # timesheet row can be validated without joining through the stage.
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    due_date = Column(Date, nullable=True)
    status = Column(String, nullable=False, default="pending")  # pending | in-progress | completed

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    completed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_role = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    stage = relationship("ProjectStage", back_populates="subtasks")


# Employee dashboards query "my project's subtask deadlines" by project + date.
Index("ix_stage_subtasks_project_due", StageSubtask.project_id, StageSubtask.due_date)
