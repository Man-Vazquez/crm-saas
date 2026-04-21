"""add_external_id_to_messages

Revision ID: a1b2c3d4e5f6
Revises: e1f2a3b4c5d6
Create Date: 2026-04-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Columna nullable — mensajes manuales y notas internas no tienen external_id.
    op.add_column(
        'messages',
        sa.Column('external_id', sa.String(500), nullable=True),
    )

    # Índice único parcial: solo aplica cuando external_id IS NOT NULL.
    # Los NULL no participan en el índice, por lo que múltiples mensajes sin
    # external_id (manuales) no generan conflicto.
    # Un statement por op.execute() — asyncpg rechaza múltiples statements en una llamada.
    op.execute(sa.text(
        "CREATE UNIQUE INDEX uq_messages_tenant_external_id "
        "ON messages(tenant_id, external_id) "
        "WHERE external_id IS NOT NULL"
    ))


def downgrade() -> None:
    op.execute(sa.text(
        "DROP INDEX IF EXISTS uq_messages_tenant_external_id"
    ))
    op.drop_column('messages', 'external_id')
