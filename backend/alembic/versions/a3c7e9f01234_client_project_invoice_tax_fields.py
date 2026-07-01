"""client type/pan/address fields, project display_name, invoice tax brackets

Revision ID: a3c7e9f01234
Revises: f1a2b3c4d5e6
Create Date: 2026-07-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a3c7e9f01234"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Clients ──
    op.add_column("clients", sa.Column("customer_type", sa.String(), nullable=False, server_default="business"))
    op.add_column("clients", sa.Column("pan", sa.String(), nullable=True))
    op.add_column("clients", sa.Column("salutation", sa.String(), nullable=True))
    op.add_column("clients", sa.Column("address_line1", sa.String(), nullable=True))
    op.add_column("clients", sa.Column("address_line2", sa.String(), nullable=True))
    op.add_column("clients", sa.Column("city", sa.String(), nullable=True))
    op.add_column("clients", sa.Column("state", sa.String(), nullable=True))
    op.add_column("clients", sa.Column("pincode", sa.String(), nullable=True))

    # ── Projects ──
    op.add_column("projects", sa.Column("display_name", sa.String(), nullable=True))

    # ── Invoices ──
    op.add_column("invoices", sa.Column("bill_to_pan", sa.String(), nullable=True))
    op.add_column("invoices", sa.Column("customer_type", sa.String(), nullable=True))
    op.add_column("invoices", sa.Column("tax_breakdown", sa.JSON(), nullable=True))

    # ── Invoice items ──
    op.add_column("invoice_items", sa.Column("tax_rate", sa.Numeric(5, 2), nullable=False, server_default="18"))


def downgrade() -> None:
    op.drop_column("invoice_items", "tax_rate")
    op.drop_column("invoices", "tax_breakdown")
    op.drop_column("invoices", "customer_type")
    op.drop_column("invoices", "bill_to_pan")
    op.drop_column("projects", "display_name")
    op.drop_column("clients", "pincode")
    op.drop_column("clients", "state")
    op.drop_column("clients", "city")
    op.drop_column("clients", "address_line2")
    op.drop_column("clients", "address_line1")
    op.drop_column("clients", "salutation")
    op.drop_column("clients", "pan")
    op.drop_column("clients", "customer_type")
