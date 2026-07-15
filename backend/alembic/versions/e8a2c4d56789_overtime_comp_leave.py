"""overtime comp-off leave ledger + leave consumption column

Overtime days (11h+ = 0.5 day, 13h+ = 1.0 day) earn comp-off leave valid 40 days
from the work date; leave approval draws these down soonest-expiry first.

Revision ID: e8a2c4d56789
Revises: d7f1a2b34567
Create Date: 2026-07-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e8a2c4d56789"
down_revision: Union[str, Sequence[str], None] = "d7f1a2b34567"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "overtime_leaves",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("timesheet_id", sa.Integer(), nullable=True),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("hours", sa.Numeric(6, 2), nullable=False),
        sa.Column("amount", sa.Numeric(3, 1), nullable=False),
        sa.Column("consumed", sa.Numeric(3, 1), nullable=False, server_default="0"),
        sa.Column("expires_on", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["employee_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["timesheet_id"], ["weekly_timesheets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("timesheet_id", "work_date", name="uq_overtime_ts_day"),
    )
    op.create_index("ix_overtime_employee", "overtime_leaves", ["employee_id"])
    op.add_column("leave_requests", sa.Column("overtime_consumed", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("leave_requests", "overtime_consumed")
    op.drop_index("ix_overtime_employee", table_name="overtime_leaves")
    op.drop_table("overtime_leaves")
