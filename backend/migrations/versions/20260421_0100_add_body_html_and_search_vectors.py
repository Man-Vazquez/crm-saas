"""add_body_html_and_search_vectors

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-04-21 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a1'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── messages ──────────────────────────────────────────────────────────
    op.add_column('messages', sa.Column('body_html', sa.Text, nullable=True))
    op.add_column('messages', sa.Column('search_vector', sa.dialects.postgresql.TSVECTOR, nullable=True))

    op.execute(sa.text(
        "CREATE INDEX ix_messages_search_vector ON messages USING GIN(search_vector)"
    ))

    # Una sola instrucción CREATE FUNCTION por op.execute — el cuerpo PL/pgSQL
    # usa $$...$$, que son literales de string, no statements separados.
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION messages_search_vector_update() RETURNS trigger AS $$
        BEGIN
          NEW.search_vector := to_tsvector('spanish', coalesce(NEW.body, ''));
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """))

    op.execute(sa.text(
        "CREATE TRIGGER messages_search_vector_trigger "
        "BEFORE INSERT OR UPDATE ON messages "
        "FOR EACH ROW EXECUTE FUNCTION messages_search_vector_update()"
    ))

    # ── tickets ───────────────────────────────────────────────────────────
    op.add_column('tickets', sa.Column('search_vector', sa.dialects.postgresql.TSVECTOR, nullable=True))

    op.execute(sa.text(
        "CREATE INDEX ix_tickets_search_vector ON tickets USING GIN(search_vector)"
    ))

    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION tickets_search_vector_update() RETURNS trigger AS $$
        BEGIN
          NEW.search_vector := to_tsvector('spanish', coalesce(NEW.subject, ''));
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """))

    op.execute(sa.text(
        "CREATE TRIGGER tickets_search_vector_trigger "
        "BEFORE INSERT OR UPDATE ON tickets "
        "FOR EACH ROW EXECUTE FUNCTION tickets_search_vector_update()"
    ))

    # ── customers ─────────────────────────────────────────────────────────
    op.add_column('customers', sa.Column('search_vector', sa.dialects.postgresql.TSVECTOR, nullable=True))

    op.execute(sa.text(
        "CREATE INDEX ix_customers_search_vector ON customers USING GIN(search_vector)"
    ))

    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION customers_search_vector_update() RETURNS trigger AS $$
        BEGIN
          NEW.search_vector := to_tsvector('spanish',
            coalesce(NEW.full_name, '') || ' ' ||
            coalesce(NEW.email, '') || ' ' ||
            coalesce(NEW.company, ''));
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """))

    op.execute(sa.text(
        "CREATE TRIGGER customers_search_vector_trigger "
        "BEFORE INSERT OR UPDATE ON customers "
        "FOR EACH ROW EXECUTE FUNCTION customers_search_vector_update()"
    ))

    # ── Backfill de registros existentes ─────────────────────────────────
    op.execute(sa.text(
        "UPDATE messages SET search_vector = to_tsvector('spanish', coalesce(body, ''))"
    ))

    op.execute(sa.text(
        "UPDATE tickets SET search_vector = to_tsvector('spanish', coalesce(subject, ''))"
    ))

    op.execute(sa.text(
        "UPDATE customers SET search_vector = to_tsvector('spanish', "
        "coalesce(full_name, '') || ' ' || coalesce(email, '') || ' ' || coalesce(company, ''))"
    ))


def downgrade() -> None:
    # Triggers
    op.execute(sa.text("DROP TRIGGER IF EXISTS messages_search_vector_trigger ON messages"))
    op.execute(sa.text("DROP TRIGGER IF EXISTS tickets_search_vector_trigger ON tickets"))
    op.execute(sa.text("DROP TRIGGER IF EXISTS customers_search_vector_trigger ON customers"))

    # Functions
    op.execute(sa.text("DROP FUNCTION IF EXISTS messages_search_vector_update()"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS tickets_search_vector_update()"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS customers_search_vector_update()"))

    # Indices
    op.execute(sa.text("DROP INDEX IF EXISTS ix_messages_search_vector"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_tickets_search_vector"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_customers_search_vector"))

    # Columns
    op.drop_column('customers', 'search_vector')
    op.drop_column('tickets', 'search_vector')
    op.drop_column('messages', 'search_vector')
    op.drop_column('messages', 'body_html')
