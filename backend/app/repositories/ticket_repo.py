import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.ticket import Ticket
from app.models.ticket_config import TicketType, TicketSubtype, TicketStatus
from app.models.message import Message
from app.schemas.ticket import (
    TicketCreate, TicketUpdate,
    TicketTypeCreate, TicketSubtypeCreate, TicketStatusCreate,
)
from app.schemas.message import MessageCreate


class TicketRepository(BaseRepository):

    # --- Tipos ---

    async def create_type(self, db: AsyncSession, data: TicketTypeCreate) -> TicketType:
        obj = TicketType(tenant_id=self.tenant_id, **data.model_dump())
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return obj

    async def get_types(self, db: AsyncSession) -> list[TicketType]:
        result = await db.execute(
            select(TicketType).where(
                TicketType.tenant_id == self.tenant_id,
                TicketType.is_active == True,
            ).order_by(TicketType.name)
        )
        return result.scalars().all()

    # --- Subtipos ---

    async def create_subtype(self, db: AsyncSession, data: TicketSubtypeCreate) -> TicketSubtype:
        obj = TicketSubtype(tenant_id=self.tenant_id, **data.model_dump())
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return obj

    async def get_subtypes(self, db: AsyncSession, type_id: uuid.UUID) -> list[TicketSubtype]:
        result = await db.execute(
            select(TicketSubtype).where(
                TicketSubtype.tenant_id == self.tenant_id,
                TicketSubtype.type_id == type_id,
                TicketSubtype.is_active == True,
            ).order_by(TicketSubtype.name)
        )
        return result.scalars().all()

    # --- Estados ---

    async def create_status(self, db: AsyncSession, data: TicketStatusCreate) -> TicketStatus:
        obj = TicketStatus(tenant_id=self.tenant_id, **data.model_dump())
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return obj

    async def get_statuses(self, db: AsyncSession) -> list[TicketStatus]:
        result = await db.execute(
            select(TicketStatus).where(
                TicketStatus.tenant_id == self.tenant_id,
                TicketStatus.is_active == True,
            ).order_by(TicketStatus.sort_order)
        )
        return result.scalars().all()

    async def get_default_status(self, db: AsyncSession) -> TicketStatus | None:
        result = await db.execute(
            select(TicketStatus).where(
                TicketStatus.tenant_id == self.tenant_id,
                TicketStatus.is_default == True,
                TicketStatus.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    # --- Tickets ---

    async def create(self, db: AsyncSession, data: TicketCreate) -> Ticket:
        ticket = Ticket(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        db.add(ticket)
        await db.flush()
        await db.refresh(ticket)
        return ticket

    async def get_by_id(self, db: AsyncSession, ticket_id: uuid.UUID) -> Ticket | None:
        result = await db.execute(
            select(Ticket).where(
                Ticket.id == ticket_id,
                Ticket.tenant_id == self.tenant_id,
                Ticket.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        status_id: uuid.UUID | None = None,
        assigned_to: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
        priority: str | None = None,
    ) -> tuple[list[Ticket], int]:
        query = select(Ticket).where(
            Ticket.tenant_id == self.tenant_id,
            Ticket.is_active == True,
        )

        if status_id:
            query = query.where(Ticket.status_id == status_id)
        if assigned_to:
            query = query.where(Ticket.assigned_to == assigned_to)
        if customer_id:
            query = query.where(Ticket.customer_id == customer_id)
        if priority:
            query = query.where(Ticket.priority == priority)

        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        query = query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all(), total

    async def update(
        self,
        db: AsyncSession,
        ticket: Ticket,
        data: TicketUpdate,
        updated_by: uuid.UUID | None = None,
        activity_desc: str | None = None,
    ) -> Ticket:
        # Exclude updated_by — it is always set server-side, never from the client payload
        for field, value in data.model_dump(exclude_unset=True, exclude={'updated_by'}).items():
            setattr(ticket, field, value)
        if updated_by is not None:
            ticket.updated_by = updated_by
        if activity_desc is not None:
            ticket.last_activity = activity_desc
        await db.flush()
        await db.refresh(ticket)
        return ticket

    async def touch_activity(
        self,
        db: AsyncSession,
        ticket: Ticket,
        updated_by: uuid.UUID,
        activity_desc: str,
    ) -> None:
        """Update activity tracking fields without changing ticket business data."""
        ticket.updated_by = updated_by
        ticket.last_activity = activity_desc
        await db.flush()

    async def delete(self, db: AsyncSession, ticket: Ticket) -> Ticket:
        ticket.is_active = False
        await db.flush()
        return ticket

    # --- Mensajes ---

    async def create_message(
        self,
        db: AsyncSession,
        ticket_id: uuid.UUID,
        author_id: uuid.UUID,
        data: MessageCreate,
    ) -> Message:
        direction = "outbound"
        message = Message(
            tenant_id=self.tenant_id,
            ticket_id=ticket_id,
            author_id=author_id,
            body=data.body,
            direction=direction,
            msg_type=data.msg_type,
        )
        db.add(message)
        await db.flush()
        await db.refresh(message)
        return message

    async def get_messages(
        self,
        db: AsyncSession,
        ticket_id: uuid.UUID,
    ) -> list[Message]:
        result = await db.execute(
            select(Message).where(
                Message.tenant_id == self.tenant_id,
                Message.ticket_id == ticket_id,
            ).order_by(Message.created_at.asc())
        )
        return result.scalars().all()

    async def create_message_direct(
        self,
        db: AsyncSession,
        ticket_id: uuid.UUID,
        author_id: uuid.UUID,
        body: str,
        direction: str = "outbound",
        msg_type: str = "reply",
        metadata: dict | None = None,
    ) -> Message:
        """
        Crea un mensaje con parámetros individuales.
        Usado por ChannelService al enviar respuestas por canal.
        A diferencia de create_message, acepta metadata y dirección explícita.
        """
        message = Message(
            tenant_id=self.tenant_id,
            ticket_id=ticket_id,
            author_id=author_id,
            body=body,
            direction=direction,
            msg_type=msg_type,
            metadata=metadata or {},
        )
        db.add(message)
        await db.flush()
        await db.refresh(message)
        return message