import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
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
        return TicketResponse.model_validate(ticket)

    async def get_by_id(
        self, db: AsyncSession, ticket_id: uuid.UUID
    ) -> TicketResponse:
        ticket = await self.repo.get_by_id(db, ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket no encontrado",
            )
        return TicketResponse.model_validate(ticket)

    async def get_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        status_id: uuid.UUID | None = None,
        assigned_to: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
        priority: str | None = None,
    ) -> dict:
        tickets, total = await self.repo.get_all(
            db, skip, limit, status_id, assigned_to, customer_id, priority
        )
        return {
            "items": [TicketResponse.model_validate(t) for t in tickets],
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    async def update(
        self,
        db: AsyncSession,
        ticket_id: uuid.UUID,
        data: TicketUpdate,
    ) -> TicketResponse:
        ticket = await self.repo.get_by_id(db, ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket no encontrado",
            )
        ticket = await self.repo.update(db, ticket, data)
        return TicketResponse.model_validate(ticket)

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