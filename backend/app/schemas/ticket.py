import uuid
from pydantic import BaseModel
from datetime import datetime
from typing import Literal


# --- Configuración ---

class TicketTypeCreate(BaseModel):
    name: str
    description: str | None = None


class TicketTypeResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class TicketSubtypeCreate(BaseModel):
    name: str
    type_id: uuid.UUID


class TicketSubtypeResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    type_id: uuid.UUID
    name: str
    is_active: bool

    model_config = {"from_attributes": True}


class TicketStatusCreate(BaseModel):
    name: str
    color: str = "#6B7280"
    sort_order: int = 0
    is_default: bool = False


class TicketStatusResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    color: str
    sort_order: int
    is_default: bool
    is_active: bool

    model_config = {"from_attributes": True}


# --- Tickets ---

class TicketCreate(BaseModel):
    customer_id: uuid.UUID
    status_id: uuid.UUID
    subject: str
    channel: str = "manual"
    channel_id: uuid.UUID | None = None
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    type_id: uuid.UUID | None = None
    subtype_id: uuid.UUID | None = None
    assigned_to: uuid.UUID | None = None


class TicketUpdate(BaseModel):
    status_id: uuid.UUID | None = None
    subject: str | None = None
    priority: Literal["low", "medium", "high", "urgent"] | None = None
    type_id: uuid.UUID | None = None
    subtype_id: uuid.UUID | None = None
    assigned_to: uuid.UUID | None = None
    resolved_at: datetime | None = None
    updated_by: uuid.UUID | None = None  # set server-side from current_user; ignored if sent by client


class TicketResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    assigned_to: uuid.UUID | None
    status_id: uuid.UUID
    type_id: uuid.UUID | None
    subtype_id: uuid.UUID | None
    subject: str
    channel: str
    channel_id: uuid.UUID | None
    priority: str
    is_active: bool
    resolved_at: datetime | None
    ticket_number: int | None
    updated_by: uuid.UUID | None
    last_activity: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}