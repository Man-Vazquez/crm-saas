import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum, text as sa_text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.core.database import Base


class PlanType(str, enum.Enum):
    """
    Planes disponibles del SaaS.
    Hereda de str para que sea serializable a JSON directamente.
    Agregar un plan nuevo es tan simple como agregar una línea aquí.
    """
    FREE       = "free"
    STARTER    = "starter"
    GROWTH     = "growth"
    ENTERPRISE = "enterprise"


class Tenant(Base):
    """
    Representa una empresa/cuenta en el sistema.
    Es la raíz de toda la jerarquía multitenant.
    Cada fila en esta tabla es un cliente tuyo.
    """
    __tablename__ = "tenants"

    # ── Identidad ─────────────────────────────────────────────────────
    # server_default genera el UUID en PostgreSQL, no en Python.
    # Ventaja: si insertas múltiples filas en una transacción,
    # cada una tiene su UUID sin coordinación entre procesos.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa_text("gen_random_uuid()"),   # función nativa de PostgreSQL 13+
    )

    # ── Datos de la cuenta ────────────────────────────────────────────
    # name: el nombre visible. "Empresa Acme S.A."
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # slug: identificador URL-friendly. "empresa-acme"
    # Lo usaremos para identificar el tenant en el subdominio o en el header.
    # unique=True + index=True porque lo buscamos en cada request.
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    # plan: qué suscripción tiene este tenant
    plan: Mapped[PlanType] = mapped_column(
        SAEnum(PlanType, name="plan_type", create_type=False, values_callable=lambda x: [e.value for e in x],),
        nullable=False,
        default=PlanType.FREE,
    )

    # ── Estado ────────────────────────────────────────────────────────
    # is_active=False en lugar de borrar el tenant.
    # Nunca borramos tenants — pueden tener datos históricos importantes
    # y las FKs de otras tablas los referencian.
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # ── Timestamps ────────────────────────────────────────────────────
    # timezone=True guarda en UTC siempre. Nunca guardes fechas sin timezone
    # en una app que puede tener usuarios en distintos países.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Tenant id={self.id} slug={self.slug} plan={self.plan}>"