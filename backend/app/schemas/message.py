import uuid
from pydantic import BaseModel
from datetime import datetime
from typing import Literal


class MessageCreate(BaseModel):
    body: str
    msg_type: Literal["reply", "comment"] = "reply"


class MessageResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    ticket_id: uuid.UUID
    author_id: uuid.UUID | None
    body: str
    direction: str
    msg_type: str
    metadata_: dict
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}