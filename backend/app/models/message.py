import uuid
from sqlalchemy import String, ForeignKey, Text, TIMESTAMP, text as sa_text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR
from datetime import datetime, timezone
from app.core.database import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=sa_text("gen_random_uuid()")
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False, index=True
    )
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False, default="outbound")
    msg_type: Mapped[str] = mapped_column(String(20), nullable=False, default="reply")
    # ID del mensaje en el canal de origen (Message-ID de email, msg_id de WhatsApp).
    # Nullable: mensajes manuales y notas internas no tienen external_id.
    # El índice parcial uq_messages_tenant_external_id garantiza unicidad por tenant
    # solo cuando external_id IS NOT NULL (los NULL no se comparan entre sí en SQL).
    external_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # HTML original del email para renderizado en el frontend. body contiene texto plano
    # para búsqueda full-text. Null para mensajes manuales y notas internas.
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Vector de búsqueda full-text. Actualizado automáticamente por trigger de PostgreSQL.
    # En tests hay que actualizar manualmente (los triggers no se crean con create_all).
    search_vector: Mapped[str | None] = mapped_column(TSVECTOR, nullable=True)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )