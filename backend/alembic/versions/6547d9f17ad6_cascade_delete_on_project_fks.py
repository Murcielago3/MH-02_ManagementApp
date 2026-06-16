"""cascade_delete_on_project_fks

Revision ID: 6547d9f17ad6
Revises: 4bd225e6dadd
Create Date: 2026-05-27 08:57:53.349215

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6547d9f17ad6'
down_revision: Union[str, Sequence[str], None] = '4bd225e6dadd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # project_assignments.project_id → CASCADE
    op.drop_constraint('project_assignments_project_id_fkey', 'project_assignments', type_='foreignkey')
    op.create_foreign_key('project_assignments_project_id_fkey', 'project_assignments', 'projects', ['project_id'], ['id'], ondelete='CASCADE')

    # timesheets.project_id → CASCADE
    op.drop_constraint('timesheets_project_id_fkey', 'timesheets', type_='foreignkey')
    op.create_foreign_key('timesheets_project_id_fkey', 'timesheets', 'projects', ['project_id'], ['id'], ondelete='CASCADE')

    # tasks.project_id → CASCADE
    op.drop_constraint('tasks_project_id_fkey', 'tasks', type_='foreignkey')
    op.create_foreign_key('tasks_project_id_fkey', 'tasks', 'projects', ['project_id'], ['id'], ondelete='CASCADE')

    # invoices.project_id → SET NULL (invoice survives project deletion)
    op.drop_constraint('invoices_project_id_fkey', 'invoices', type_='foreignkey')
    op.create_foreign_key('invoices_project_id_fkey', 'invoices', 'projects', ['project_id'], ['id'], ondelete='SET NULL')

    # weekly_timesheet_entries.project_id → SET NULL
    op.drop_constraint('weekly_timesheet_entries_project_id_fkey', 'weekly_timesheet_entries', type_='foreignkey')
    op.create_foreign_key('weekly_timesheet_entries_project_id_fkey', 'weekly_timesheet_entries', 'projects', ['project_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('project_assignments_project_id_fkey', 'project_assignments', type_='foreignkey')
    op.create_foreign_key('project_assignments_project_id_fkey', 'project_assignments', 'projects', ['project_id'], ['id'])

    op.drop_constraint('timesheets_project_id_fkey', 'timesheets', type_='foreignkey')
    op.create_foreign_key('timesheets_project_id_fkey', 'timesheets', 'projects', ['project_id'], ['id'])

    op.drop_constraint('tasks_project_id_fkey', 'tasks', type_='foreignkey')
    op.create_foreign_key('tasks_project_id_fkey', 'tasks', 'projects', ['project_id'], ['id'])

    op.drop_constraint('invoices_project_id_fkey', 'invoices', type_='foreignkey')
    op.create_foreign_key('invoices_project_id_fkey', 'invoices', 'projects', ['project_id'], ['id'])

    op.drop_constraint('weekly_timesheet_entries_project_id_fkey', 'weekly_timesheet_entries', type_='foreignkey')
    op.create_foreign_key('weekly_timesheet_entries_project_id_fkey', 'weekly_timesheet_entries', 'projects', ['project_id'], ['id'])
