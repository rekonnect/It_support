"""add scheduled_tasks table

Revision ID: a1b2c3d4e5f6
Revises: 0c7ee2e20ca1
Create Date: 2025-08-11 19:03:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '0c7ee2e20ca1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('scheduled_tasks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('task_type', sa.String(), nullable=False),
    sa.Column('target', sa.String(), nullable=False),
    sa.Column('cron_schedule', sa.String(), nullable=False),
    sa.Column('is_enabled', sa.Boolean(), nullable=True),
    sa.Column('details', sa.JSON(), nullable=True),
    sa.Column('tenant_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scheduled_tasks_id'), 'scheduled_tasks', ['id'], unique=False)
    op.create_index(op.f('ix_scheduled_tasks_name'), 'scheduled_tasks', ['name'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_scheduled_tasks_name'), table_name='scheduled_tasks')
    op.drop_index(op.f('ix_scheduled_tasks_id'), table_name='scheduled_tasks')
    op.drop_table('scheduled_tasks')
