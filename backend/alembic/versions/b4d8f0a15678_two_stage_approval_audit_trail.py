"""two-stage timesheet approval + audit trail

Revision ID: b4d8f0a15678
Revises: a3c7e9f01234
Create Date: 2026-07-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b4d8f0a15678"
down_revision: Union[str, Sequence[str], None] = "a3c7e9f01234"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Two-stage approval slots on weekly timesheets
    op.add_column("weekly_timesheets", sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("weekly_timesheets", sa.Column("pm_approved_by", sa.Integer(), nullable=True))
    op.add_column("weekly_timesheets", sa.Column("pm_approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("weekly_timesheets", sa.Column("admin_approved_by", sa.Integer(), nullable=True))
    op.add_column("weekly_timesheets", sa.Column("admin_approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("weekly_timesheets", sa.Column("rejected_by", sa.Integer(), nullable=True))
    op.add_column("weekly_timesheets", sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True))

    # Pre-existing approved timesheets are fully approved: fill both slots so
    # they keep counting toward cost/reserve under the new derived status.
    op.execute(
        "UPDATE weekly_timesheets SET "
        "pm_approved_at = COALESCE(pm_approved_at, NOW()), "
        "admin_approved_at = COALESCE(admin_approved_at, NOW()) "
        "WHERE status = 'approved'"
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("actor_name", sa.String(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("entity_type", sa.String(), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_entity_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_table("audit_logs")
    for col in ("rejected_at", "rejected_by", "admin_approved_at", "admin_approved_by",
                "pm_approved_at", "pm_approved_by", "submitted_at"):
        op.drop_column("weekly_timesheets", col)
