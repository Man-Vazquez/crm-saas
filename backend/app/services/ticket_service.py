import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.department import Department
from app.repositories.ticket_repo import TicketRepository
from app.schemas.ticket import (
    TicketCreate, TicketUpdate, TicketResponse,
    TicketTypeCreate, TicketTypeResponse,
    TicketSubtypeCreate, TicketSubtypeResponse,
    TicketStatusCreate, TicketStatusResponse,
)
from app.schemas.message import MessageCreate, MessageResponse


class TicketService:

    def __init__(self, tenant_id: uuid.UUID):
        self.repo = TicketRepository(tenant_id)

    # --- Helpers ---

    @staticmethod
    async def _department_name(db: AsyncSession, department_id: uuid.UUID | None) -> str | None:
        """Fetch department name for a single department_id. Returns None if not set."""
        if not department_id:
            return None
        result = await db.execute(
            select(Department.name).where(Department.id == department_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _department_names_batch(
        db: AsyncSession, tickets: list
    ) -> dict[uuid.UUID, str]:
        """Fetch department names for a list of tickets in a single query."""
        dept_ids = {t.department_id for t in tickets if t.department_id}
        if not dept_ids:
            return {}
        rows = (await db.execute(
            select(Department.id, Department.name).where(Department.id.in_(dept_ids))
        )).all()
        return {r[0]: r[1] for r in rows}

    # --- Tipos ---

    async def create_type(
        self, db: AsyncSession, data: TicketTypeCreate
    ) -> TicketTypeResponse:
        obj = await self.repo.create_type(db, data)
        return TicketTypeResponse.model_validate(obj)

    async def get_types(self, db: AsyncSession) -> list[TicketTypeResponse]:
        items = await self.repo.get_types(db)
        return [TicketTypeResponse.model_validate(i) for i in items]

    # --- Subtipos ---

    async def create_subtype(
        self, db: AsyncSession, data: TicketSubtypeCreate
    ) -> TicketSubtypeResponse:
        obj = await self.repo.create_subtype(db, data)
        return TicketSubtypeResponse.model_validate(obj)

    async def get_subtypes(
        self, db: AsyncSession, type_id: uuid.UUID
    ) -> list[TicketSubtypeResponse]:
        items = await self.repo.get_subtypes(db, type_id)
        return [TicketSubtypeResponse.model_validate(i) for i in items]

    # --- Estados ---

    async def create_status(
        self, db: AsyncSession, data: TicketStatusCreate
    ) -> TicketStatusResponse:
        obj = await self.repo.create_status(db, data)
        return TicketStatusResponse.model_validate(obj)

    async def get_statuses(self, db: AsyncSession) -> list[TicketStatusResponse]:
        items = await self.repo.get_statuses(db)
        return [TicketStatusResponse.model_validate(i) for i in items]

    # --- Tickets ---

    async def create(
        self, db: AsyncSession, data: TicketCreate
    ) -> TicketResponse:
        # Verificar que el status_id pertenece al tenant
        statuses = await self.repo.get_statuses(db)
        status_ids = [s.id for s in statuses]
        if data.status_id not in status_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estado de ticket inválido para este tenant",
            )
        ticket = await self.repo.create(db, data)
        dept_name = await self._department_name(db, ticket.department_id)
        return TicketResponse.model_validate(ticket).model_copy(
            update={'department_name': dept_name}
        )

    async def get_by_id(
        self, db: AsyncSession, ticket_id: uuid.UUID
    ) -> TicketResponse:
        ticket = await self.repo.get_by_id(db, ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket no encontrado",
            )
        dept_name = await self._department_name(db, ticket.department_id)
        return TicketResponse.model_validate(ticket).model_copy(
            update={'department_name': dept_name}
        )

    async def get_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        status_id: uuid.UUID | None = None,
        assigned_to: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
        priority: str | None = None,
        department_id: uuid.UUID | None = None,
    ) -> dict:
        tickets, total = await self.repo.get_all(
            db, skip, limit, status_id, assigned_to, customer_id, priority, department_id
        )
        dept_names = await self._department_names_batch(db, tickets)
        items = [
            TicketResponse.model_validate(t).model_copy(
                update={'department_name': dept_names.get(t.department_id)}
            )
            for t in tickets
        ]
        return {"items": items, "total": total, "skip": skip, "limit": limit}

    @staticmethod
    def _activity_from_update(data: TicketUpdate) -> str:
        changed = data.model_dump(exclude_unset=True, exclude={'updated_by'})
        PRIORITY_ES = {'low': 'Baja', 'medium': 'Media', 'high': 'Alta', 'urgent': 'Urgente'}
        if 'priority' in changed and changed['priority']:
            return f"Prioridad cambiada a {PRIORITY_ES.get(changed['priority'], changed['priority'])}"
        if 'status_id' in changed:
            return "Estado actualizado"
        if 'assigned_to' in changed:
            return "Ticket asignado" if changed['assigned_to'] else "Ticket desasignado"
        if 'department_id' in changed:
            return "Departamento actualizado" if changed['department_id'] else "Departamento eliminado"
        if 'type_id' in changed:
            return "Tipo actualizado"
        if 'subtype_id' in changed:
            return "Subtipo actualizado"
        if 'subject' in changed:
            return "Asunto actualizado"
        return "Ticket actualizado"

    async def update(
        self,
        db: AsyncSession,
        ticket_id: uuid.UUID,
        data: TicketUpdate,
        updated_by: uuid.UUID | None = None,
    ) -> TicketResponse:
        ticket = await self.repo.get_by_id(db, ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket no encontrado",
            )
        activity_desc = self._activity_from_update(data)
        ticket = await self.repo.update(db, ticket, data, updated_by=updated_by, activity_desc=activity_desc)
        dept_name = await self._department_name(db, ticket.department_id)
        return TicketResponse.model_validate(ticket).model_copy(
            update={'department_name': dept_name}
        )

    async def touch_activity(
        self,
        db: AsyncSession,
        ticket_id: uuid.UUID,
        updated_by: uuid.UUID,
        activity_desc: str,
    ) -> None:
        ticket = await self.repo.get_by_id(db, ticket_id)
        if ticket:
            await self.repo.touch_activity(db, ticket, updated_by, activity_desc)

    async def delete(self, db: AsyncSession, ticket_id: uuid.UUID) -> dict:
        ticket = await self.repo.get_by_id(db, ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket no encontrado",
            )
        await self.repo.delete(db, ticket)
        return {"message": "Ticket eliminado correctamente"}

    # --- Mensajes ---

    async def create_message(
        self,
        db: AsyncSession,
        ticket_id: uuid.UUID,
        author_id: uuid.UUID,
        data: MessageCreate,
    ) -> MessageResponse:
        ticket = await self.repo.get_by_id(db, ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket no encontrado",
            )
        message = await self.repo.create_message(db, ticket_id, author_id, data)
        activity_desc = "Respuesta enviada" if data.msg_type == "reply" else "Nota interna agregada"
        await self.repo.touch_activity(db, ticket, author_id, activity_desc)
        return MessageResponse.model_validate(message)

    async def get_messages(
        self,
        db: AsyncSession,
        ticket_id: uuid.UUID,
    ) -> list[MessageResponse]:
        ticket = await self.repo.get_by_id(db, ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket no encontrado",
            )
        messages = await self.repo.get_messages(db, ticket_id)
        return [MessageResponse.model_validate(m) for m in messages]