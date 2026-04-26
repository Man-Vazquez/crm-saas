from uuid import UUID
from pydantic import BaseModel
from datetime import datetime


class ChannelCreate(BaseModel):
    channel_type: str           # "email" | "whatsapp"
    name: str                   # "Email soporte", "WhatsApp ventas"
    config: dict                # credenciales — se encriptan antes de guardar
    department_id: UUID | None = None


class ChannelUpdate(BaseModel):
    name: str | None = None
    config: dict | None = None
    is_active: bool | None = None
    department_id: UUID | None = None


class ChannelResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    channel_type: str
    name: str
    is_active: bool
    department_id: UUID | None
    created_at: datetime

    # config NO se devuelve en la response — nunca exponemos credenciales
    model_config = {"from_attributes": True}


class AgentChannelCreate(BaseModel):
    agent_id: UUID
    channel_id: UUID


class AgentChannelResponse(BaseModel):
    id: UUID
    agent_id: UUID
    channel_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}