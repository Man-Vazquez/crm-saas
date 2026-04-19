from pydantic import BaseModel


class TicketsByStatusItem(BaseModel):
    status_name: str
    color: str
    count: int


class TicketsByPriorityItem(BaseModel):
    priority: str
    count: int


class TicketsByChannelItem(BaseModel):
    channel: str
    count: int


class TicketsByAgentItem(BaseModel):
    agent_name: str
    total: int
    open: int
    resolved: int


class TicketsByTypeItem(BaseModel):
    type_name: str
    subtype_name: str | None
    count: int


class DailyTicketsItem(BaseModel):
    date: str
    count: int


class DashboardSummary(BaseModel):
    total_open: int
    total_in_progress: int
    total_resolved: int
    total_closed: int
    avg_resolution_hours: float | None
