from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class DepartmentCreate(BaseModel):
    name: str
    description: str | None = None


class DepartmentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class DepartmentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    agent_count: int = 0
    channel_count: int = 0


class AgentAddRequest(BaseModel):
    user_id: UUID


class DepartmentAgentResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
