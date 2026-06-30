"""add salary history + frozen timesheet entry cost

Revision ID: f1a2b3c4d5e6
Revises: 9b92c826420c
Create Date: 2026-06-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "9b92c826420c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "salary_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("monthly_salary", sa.Numeric(10, 2), nullable=True),
        sa.Column("salary_hour", sa.Numeric(8, 2), nullable=True),
        sa.Column("smpy", sa.Numeric(4, 2), nullable=True),
        sa.Column("whpm", sa.Numeric(6, 2), nullable=True),
        sa.Column("hourly_rate", sa.Numeric(10, 2), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "effective_from", name="uq_salary_user_effrom"),
    )
    op.create_index("ix_salary_history_user_id", "salary_history", ["user_id"])
    op.add_column("weekly_timesheet_entries", sa.Column("employee_cost", sa.Numeric(12, 2), nullable=True))
    op.add_column("weekly_timesheet_entries", sa.Column("cost_breakdown", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("weekly_timesheet_entries", "cost_breakdown")
    op.drop_column("weekly_timesheet_entries", "employee_cost")
    op.drop_index("ix_salary_history_user_id", table_name="salary_history")
    op.drop_table("salary_history")
