"""reimbursement submission timestamp (created_at)

Basis for which salary-slip month a claim rolls into: the submission month's
slip, which pays out the following month.

Revision ID: c5e9a1b23456
Revises: b4d8f0a15678
Create Date: 2026-07-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c5e9a1b23456"
down_revision: Union[str, Sequence[str], None] = "b4d8f0a15678"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "reimbursements",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # Backfill existing rows from the expense date so historical claims have a
    # sensible submission month to bundle under.
    op.execute("UPDATE reimbursements SET created_at = date::timestamp WHERE created_at IS NULL")


def downgrade() -> None:
    op.drop_column("reimbursements", "created_at")
