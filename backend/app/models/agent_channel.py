from __future__ import annotations
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import ForeignKey, TIMESTAMP, UniqueConstraint, text as sa_text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class AgentChannel(Base):
    """
    Tabla intermedia: qué agentes tienen acceso a qué canales.
    Si un canal no tiene agentes asignados → todos los agentes del tenant lo ven.
    Si tiene agentes asignados → solo esos agentes lo ven.
    """
    __tablename__ = "agent_channels"
    __table_args__ = (
        UniqueConstraint("agent_id", "channel_id", name="uq_agent_channel"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=sa_text("gen_random_uuid()"),
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    channel_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )