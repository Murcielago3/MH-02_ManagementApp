"""timesheet_project_fk_set_null

Revision ID: 9b92c826420c
Revises: 6547d9f17ad6
Create Date: 2026-05-27 08:59:49.971263

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b92c826420c'
down_revision: Union[str, Sequence[str], None] = '6547d9f17ad6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Change timesheets.project_id from CASCADE → SET NULL, also make nullable
    op.drop_constraint('timesheets_project_id_fkey', 'timesheets', type_='foreignkey')
    op.alter_column('timesheets', 'project_id', nullable=True)
    op.create_foreign_key('timesheets_project_id_fkey', 'timesheets', 'projects', ['project_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('timesheets_project_id_fkey', 'timesheets', type_='foreignkey')
    op.alter_column('timesheets', 'project_id', nullable=False)
    op.create_foreign_key('timesheets_project_id_fkey', 'timesheets', 'projects', ['project_id'], ['id'], ondelete='CASCADE')
