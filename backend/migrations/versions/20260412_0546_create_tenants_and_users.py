"""create tenants and users

Revision ID: 9300d350c575
Revises: 
Create Date: 2026-04-12 05:46:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '9300d350c575'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TYPE plan_type AS ENUM ('free', 'starter', 'growth', 'enterprise')
    """)
    op.execute("""
        CREATE TYPE user_role AS ENUM ('admin', 'supervisor', 'agent')
    """)
    op.execute("""
        CREATE TABLE tenants (
            id          UUID        NOT NULL DEFAULT gen_random_uuid(),
            name        VARCHAR(255) NOT NULL,
            slug        VARCHAR(100) NOT NULL,
            plan        plan_type   NOT NULL DEFAULT 'free',
            is_active   BOOLEAN     NOT NULL DEFAULT true,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (id)
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX ix_tenants_slug ON tenants (slug)
    """)
    op.execute("""
        CREATE TABLE users (
            id               UUID        NOT NULL DEFAULT gen_random_uuid(),
            tenant_id        UUID        NOT NULL,
            email            VARCHAR(255) NOT NULL,
            hashed_password  VARCHAR(255) NOT NULL,
            full_name        VARCHAR(255) NOT NULL,
            role             user_role   NOT NULL DEFAULT 'agent',
            is_active        BOOLEAN     NOT NULL DEFAULT true,
            created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
            last_login_at    TIMESTAMPTZ,
            PRIMARY KEY (id),
            CONSTRAINT fk_users_tenant FOREIGN KEY (tenant_id)
                REFERENCES tenants (id) ON DELETE RESTRICT,
            CONSTRAINT uq_users_tenant_email UNIQUE (tenant_id, email)
        )
    """)
    op.execute("""
        CREATE INDEX ix_users_tenant_id ON users (tenant_id)
    """)
    op.execute("""
        CREATE INDEX ix_users_email ON users (email)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP TABLE IF EXISTS tenants")
    op.execute("DROP TYPE IF EXISTS user_role")
    op.execute("DROP TYPE IF EXISTS plan_type")