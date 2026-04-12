import uuid
from pydantic import BaseModel, EmailStr
from datetime import datetime


class CustomerCreate(BaseModel):
    full_name: str
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    notes: str | None = None
    custom_fields: dict = {}


class CustomerUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    notes: str | None = None
    custom_fields: dict | None = None


class CustomerResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    full_name: str
    email: str | None
    phone: str | None
    company: str | None
    notes: str | None
    custom_fields: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}