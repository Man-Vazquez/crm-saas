from __future__ import annotations
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import String, Boolean, ForeignKey, TIMESTAMP, Text, text as sa_text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Channel(Base):
    __tablename__ = "channels"

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

    # Tipo de canal: "email" | "whatsapp" — extendible a "messenger", "sms", etc.
    channel_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Nombre visible para el agente: "Email soporte", "WhatsApp ventas"
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Credenciales y config del canal — cada tipo tiene su propio schema de config
    # Email:     { "smtp_host", "smtp_port", "smtp_user", "smtp_pass", "from_email" }
    # WhatsApp:  { "phone_number_id", "access_token", "verify_token" }
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )