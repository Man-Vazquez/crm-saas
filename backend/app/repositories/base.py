# backend/app/repositories/base.py

from typing import Generic, TypeVar, Type, Sequence
from uuid import UUID
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base
from app.core.tenant import get_tenant_id

# Generic type para que el repositorio base funcione con cualquier modelo
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Repositorio genérico con filtro de tenant automático.

    Todo repositorio concreto hereda de este.
    Nunca escriben WHERE tenant_id = X — está aquí, una sola vez.

    Uso:
        class TicketRepository(BaseRepository[Ticket]):
            model = Ticket
    """

    model: Type[ModelType]  # las subclases definen esto

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Propiedad que todos los queries usan ──────────────────────────
    @property
    def tenant_id(self) -> UUID:
        """
        Lee el tenant_id del contexto actual.
        Si no hay tenant (bug en el flujo), lanza RuntimeError.
        """
        return get_tenant_id()

    # ── Queries base con tenant automático ───────────────────────────

    async def get_by_id(self, id: UUID) -> ModelType | None:
        """Busca por ID dentro del tenant actual. Nunca devuelve datos de otro tenant."""
        result = await self.db.execute(
            select(self.model).where(
                self.model.id == id,
                self.model.tenant_id == self.tenant_id,  # ← siempre presente
            )
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[ModelType]:
        """Lista todos los registros del tenant actual con paginación."""
        result = await self.db.execute(
            select(self.model)
            .where(self.model.tenant_id == self.tenant_id)
            .limit(limit)
            .offset(offset)
            .order_by(self.model.created_at.desc())
        )
        return result.scalars().all()

    async def create(self, **kwargs) -> ModelType:
        """
        Crea un nuevo registro.
        tenant_id se inyecta automáticamente — el caller no necesita pasarlo.
        """
        instance = self.model(
            tenant_id=self.tenant_id,  # ← inyección automática
            **kwargs,
        )
        self.db.add(instance)
        await self.db.flush()   # obtiene el ID generado sin hacer commit
                                # el commit lo hace get_db() al cerrar la session
        return instance

    async def update(self, id: UUID, **kwargs) -> ModelType | None:
        """Actualiza un registro verificando que pertenezca al tenant actual."""
        await self.db.execute(
            update(self.model)
            .where(
                self.model.id == id,
                self.model.tenant_id == self.tenant_id,
            )
            .values(**kwargs)
        )
        await self.db.flush()
        return await self.get_by_id(id)

    async def soft_delete(self, id: UUID) -> bool:
        """
        Desactiva un registro en lugar de borrarlo.
        En un SaaS los datos históricos importan — nunca hard delete.
        """
        result = await self.db.execute(
            update(self.model)
            .where(
                self.model.id == id,
                self.model.tenant_id == self.tenant_id,
            )
            .values(is_active=False)
        )
        return result.rowcount > 0