import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    """
    Roles del sistema para el MVP.
    Diseñado para expandirse — en el futuro puede ser una tabla
    propia con permisos granulares configurables por tenant.
    """
    ADMIN      = "admin"       # gestiona usuarios, configura el tenant
    SUPERVISOR = "supervisor"  # ve todos los tickets, genera reportes
    AGENT      = "agent"       # atiende tickets asignados


class User(Base):
    """
    Usuario del sistema. Siempre pertenece a un Tenant.
    Un usuario no puede existir sin tenant — es parte del diseño multitenant.
    """
    __tablename__ = "users"

    # ── Identidad ─────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default="gen_random_uuid()",
    )

    # ── Relación con Tenant ───────────────────────────────────────────
    # ForeignKey apunta a tenants.id.
    # ondelete="RESTRICT" evita borrar un tenant que tiene usuarios.
    # index=True porque filtramos por tenant_id en absolutamente todos los queries.
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # ── Datos del usuario ─────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    # email único POR TENANT, no globalmente.
    # El mismo email puede existir en dos tenants distintos.
    # Esto lo implementamos como un UniqueConstraint compuesto
    # en la migración de Alembic.

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", create_type=False, values_callable=lambda x: [e.value for e in x],),
        nullable=False,
        default=UserRole.AGENT,
    )

    # ── Estado ────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # ── Timestamps ────────────────────────────────────────────────────
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

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,    # None hasta que el usuario haga login por primera vez
    )

    # ── Relaciones ORM ────────────────────────────────────────────────
    # Esto no crea columnas — le dice a SQLAlchemy cómo hacer JOINs.
    # user.tenant te da el objeto Tenant completo sin escribir SQL.
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        lazy="selectin",    # carga el tenant automáticamente en un SELECT separado
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"