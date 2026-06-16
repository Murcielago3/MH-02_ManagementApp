"""merge_teams_into_main

Revision ID: 4bd225e6dadd
Revises: 40d4356d50ae, e1b4f2a8c911
Create Date: 2026-05-26 09:43:26.846788

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4bd225e6dadd'
down_revision: Union[str, Sequence[str], None] = ('40d4356d50ae', 'e1b4f2a8c911')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
