"""add_departments

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a1
Create Date: 2026-04-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── departments ───────────────────────────────────────────────────────────
    op.create_table(
        'departments',
        sa.Column('id', PGUUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('tenant_id', PGUUID(as_uuid=True),
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
    )

    op.execute(sa.text(
        "CREATE INDEX ix_departments_tenant_id ON departments(tenant_id)"
    ))

    # ── department_agents ─────────────────────────────────────────────────────
    op.create_table(
        'department_agents',
        sa.Column('department_id', PGUUID(as_uuid=True),
                  sa.ForeignKey('departments.id', ondelete='CASCADE'),
                  primary_key=True, nullable=False),
        sa.Column('user_id', PGUUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'),
                  primary_key=True, nullable=False),
    )

    # ── channels: add department_id ───────────────────────────────────────────
    op.add_column(
        'channels',
        sa.Column('department_id', PGUUID(as_uuid=True),
                  sa.ForeignKey('departments.id', ondelete='SET NULL'), nullable=True),
    )

    # ── tickets: add department_id ────────────────────────────────────────────
    op.add_column(
        'tickets',
        sa.Column('department_id', PGUUID(as_uuid=True),
                  sa.ForeignKey('departments.id', ondelete='SET NULL'), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('tickets', 'department_id')
    op.drop_column('channels', 'department_id')
    op.drop_table('department_agents')
    op.drop_table('departments')
