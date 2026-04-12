"""create_core_tables_fase2

Revision ID: 1fc09bfe8c8f
Revises: 9300d350c575
Create Date: 2026-04-12 06:40:44.094112

"""
from typing import Sequence, Union
from alembic import op

revision: str = '1fc09bfe8c8f'
down_revision: Union[str, None] = '9300d350c575'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE customers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            full_name VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            phone VARCHAR(50),
            company VARCHAR(255),
            notes TEXT,
            custom_fields JSONB NOT NULL DEFAULT '{}',
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_customers_tenant_id ON customers(tenant_id)")
    op.execute("CREATE INDEX ix_customers_email ON customers(tenant_id, email)")

    op.execute("""
        CREATE TABLE ticket_types (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            name VARCHAR(100) NOT NULL,
            description TEXT,
            is_active BOOLEAN NOT NULL DEFAULT true
        )
    """)
    op.execute("CREATE INDEX ix_ticket_types_tenant_id ON ticket_types(tenant_id)")

    op.execute("""
        CREATE TABLE ticket_subtypes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            type_id UUID NOT NULL REFERENCES ticket_types(id),
            name VARCHAR(100) NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT true
        )
    """)
    op.execute("CREATE INDEX ix_ticket_subtypes_tenant_id ON ticket_subtypes(tenant_id)")
    op.execute("CREATE INDEX ix_ticket_subtypes_type_id ON ticket_subtypes(type_id)")

    op.execute("""
        CREATE TABLE ticket_statuses (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            name VARCHAR(100) NOT NULL,
            color VARCHAR(7) NOT NULL DEFAULT '#6B7280',
            sort_order INTEGER NOT NULL DEFAULT 0,
            is_default BOOLEAN NOT NULL DEFAULT false,
            is_active BOOLEAN NOT NULL DEFAULT true
        )
    """)
    op.execute("CREATE INDEX ix_ticket_statuses_tenant_id ON ticket_statuses(tenant_id)")

    op.execute("""
        CREATE TABLE tickets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            customer_id UUID NOT NULL REFERENCES customers(id),
            assigned_to UUID REFERENCES users(id),
            status_id UUID NOT NULL REFERENCES ticket_statuses(id),
            type_id UUID REFERENCES ticket_types(id),
            subtype_id UUID REFERENCES ticket_subtypes(id),
            subject VARCHAR(500) NOT NULL,
            channel VARCHAR(50) NOT NULL DEFAULT 'manual',
            priority VARCHAR(20) NOT NULL DEFAULT 'medium',
            is_active BOOLEAN NOT NULL DEFAULT true,
            resolved_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_tickets_tenant_id ON tickets(tenant_id)")
    op.execute("CREATE INDEX ix_tickets_customer_id ON tickets(customer_id)")
    op.execute("CREATE INDEX ix_tickets_assigned_to ON tickets(assigned_to)")
    op.execute("CREATE INDEX ix_tickets_status_id ON tickets(status_id)")

    op.execute("""
        CREATE TABLE messages (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            ticket_id UUID NOT NULL REFERENCES tickets(id),
            author_id UUID REFERENCES users(id),
            body TEXT NOT NULL,
            direction VARCHAR(20) NOT NULL DEFAULT 'outbound',
            msg_type VARCHAR(20) NOT NULL DEFAULT 'reply',
            metadata JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_messages_tenant_id ON messages(tenant_id)")
    op.execute("CREATE INDEX ix_messages_ticket_id ON messages(ticket_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS messages")
    op.execute("DROP TABLE IF EXISTS tickets")
    op.execute("DROP TABLE IF EXISTS ticket_statuses")
    op.execute("DROP TABLE IF EXISTS ticket_subtypes")
    op.execute("DROP TABLE IF EXISTS ticket_types")
    op.execute("DROP TABLE IF EXISTS customers")