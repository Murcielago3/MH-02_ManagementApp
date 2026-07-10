"""second admin approval slot on weekly timesheets

Non-admin timesheets require two distinct admins (four-eyes); this adds the
second-admin ("second factor") approval slot.

Revision ID: d7f1a2b34567
Revises: c5e9a1b23456
Create Date: 2026-07-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d7f1a2b34567"
down_revision: Union[str, Sequence[str], None] = "c5e9a1b23456"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("weekly_timesheets", sa.Column("admin2_approved_by", sa.Integer(), nullable=True))
    op.add_column("weekly_timesheets", sa.Column("admin2_approved_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("weekly_timesheets", "admin2_approved_at")
    op.drop_column("weekly_timesheets", "admin2_approved_by")
