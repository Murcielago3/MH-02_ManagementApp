"""fix client phone to string

Revision ID: 5aa0130482e3
Revises: 8d1deaa4a6fa
Create Date: 2026-05-05 10:13:10.127879

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5aa0130482e3'
down_revision: Union[str, Sequence[str], None] = '8d1deaa4a6fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE clients ALTER COLUMN phone TYPE VARCHAR USING phone::text")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE clients ALTER COLUMN phone TYPE INTEGER USING phone::integer")
