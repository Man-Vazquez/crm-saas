import uuid
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.middleware import get_current_user
from app.core.tenant import get_tenant_id
from app.models.user import User
from app.schemas.ticket import (
    TicketCreate, TicketUpdate, TicketResponse,
    TicketTypeCreate, TicketTypeResponse,
    TicketSubtypeCreate, TicketSubtypeResponse,
    TicketStatusCreate, TicketStatusResponse,
)
from app.schemas.message import MessageCreate, MessageResponse
from app.services.ticket_service import TicketService
from app.services.channel_service import ChannelService

router = APIRouter(prefix="/tickets", tags=["tickets"])


def get_service() -> TicketService:
    return TicketService(get_tenant_id())


# --- Configuración: tipos ---

@router.post("/types", response_model=TicketTypeResponse, status_code=201)
async def create_type(
    data: TicketTypeCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_service().create_type(db, data)


@router.get("/types", response_model=list[TicketTypeResponse])
async def list_types(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_service().get_types(db)


# --- Configuración: subtipos ---

@router.post("/subtypes", response_model=TicketSubtypeResponse, status_code=201)
async def create_subtype(
    data: TicketSubtypeCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_service().create_subtype(db, data)


@router.get("/types/{type_id}/subtypes", response_model=list[TicketSubtypeResponse])
async def list_subtypes(
    type_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_service().get_subtypes(db, type_id)


# --- Configuración: estados ---

@router.post("/statuses", response_model=TicketStatusResponse, status_code=201)
async def create_status(
    data: TicketStatusCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_service().create_status(db, data)


@router.get("/statuses", response_model=list[TicketStatusResponse])
async def list_statuses(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_service().get_statuses(db)


# --- Tickets ---

@router.post("", response_model=TicketResponse, status_code=201)
async def create_ticket(
    data: TicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_service().create(db, data)


@router.get("", response_model=dict)
async def list_tickets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status_id: uuid.UUID | None = Query(None),
    assigned_to: uuid.UUID | None = Query(None),
    customer_id: uuid.UUID | None = Query(None),
    priority: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_service().get_all(
        db, skip, limit, status_id, assigned_to, customer_id, priority
    )


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_service().get_by_id(db, ticket_id)


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: uuid.UUID,
    data: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_service().update(db, ticket_id, data)


@router.delete("/{ticket_id}")
async def delete_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_service().delete(db, ticket_id)


# --- Mensajes ---

@router.post("/{ticket_id}/messages", response_model=MessageResponse, status_code=201)
async def create_message(
    ticket_id: uuid.UUID,
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_service().create_message(db, ticket_id, current_user.id, data)


@router.get("/{ticket_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_service().get_messages(db, ticket_id)

@router.post("/{ticket_id}/reply", response_model=MessageResponse, status_code=201)
async def reply_to_ticket(
    ticket_id: UUID,
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ChannelService()
    return await service.reply_to_ticket(
        db=db,
        ticket_id=ticket_id,
        agent_id=current_user.id,
        body=data.body,
    )