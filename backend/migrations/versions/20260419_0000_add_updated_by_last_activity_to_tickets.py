"""add_updated_by_last_activity_to_tickets

Revision ID: d8e9f0a1b2c3
Revises: 7f56c2a0dd4e
Create Date: 2026-04-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'd8e9f0a1b2c3'
down_revision: Union[str, None] = '7f56c2a0dd4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'tickets',
        sa.Column('updated_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
    )
    op.add_column(
        'tickets',
        sa.Column('last_activity', sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_column('tickets', 'last_activity')
    op.drop_column('tickets', 'updated_by')
