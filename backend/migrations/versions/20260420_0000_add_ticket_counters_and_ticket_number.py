"""add_ticket_counters_and_ticket_number

Revision ID: e1f2a3b4c5d6
Revises: d8e9f0a1b2c3
Create Date: 2026-04-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, None] = 'd8e9f0a1b2c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nueva tabla de contadores por tenant
    op.create_table(
        'ticket_counters',
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), primary_key=True),
        sa.Column('last_number', sa.Integer, nullable=False, server_default='0'),
    )

    # Nueva columna en tickets
    op.add_column(
        'tickets',
        sa.Column('ticket_number', sa.Integer, nullable=True),
    )

    # Backfill: asignar número secuencial por tenant ordenado por created_at
    op.execute(sa.text("""
        UPDATE tickets SET ticket_number = sub.rn
        FROM (
            SELECT id, ROW_NUMBER() OVER (
                PARTITION BY tenant_id ORDER BY created_at ASC
            ) AS rn FROM tickets
        ) sub WHERE tickets.id = sub.id
    """))

    # Inicializar contadores con el máximo actual por tenant
    op.execute(sa.text("""
        INSERT INTO ticket_counters (tenant_id, last_number)
        SELECT tenant_id, MAX(ticket_number) FROM tickets GROUP BY tenant_id
    """))


def downgrade() -> None:
    op.drop_column('tickets', 'ticket_number')
    op.drop_table('ticket_counters')
