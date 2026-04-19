from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.metrics_repo import MetricsRepository
from app.schemas.metrics import (
    TicketsByStatusItem,
    TicketsByPriorityItem,
    TicketsByChannelItem,
    TicketsByAgentItem,
    TicketsByTypeItem,
    DailyTicketsItem,
    DashboardSummary,
)


class MetricsService:

    def __init__(self):
        self.repo = MetricsRepository()

    async def get_tickets_by_status(self, db: AsyncSession) -> list[TicketsByStatusItem]:
        return await self.repo.get_tickets_by_status(db)

    async def get_tickets_by_priority(self, db: AsyncSession) -> list[TicketsByPriorityItem]:
        return await self.repo.get_tickets_by_priority(db)

    async def get_tickets_by_channel(self, db: AsyncSession) -> list[TicketsByChannelItem]:
        return await self.repo.get_tickets_by_channel(db)

    async def get_average_resolution_time(self, db: AsyncSession) -> float | None:
        return await self.repo.get_average_resolution_time(db)

    async def get_tickets_created_last_30_days(self, db: AsyncSession) -> list[DailyTicketsItem]:
        return await self.repo.get_tickets_created_last_30_days(db)

    async def get_tickets_by_agent(self, db: AsyncSession) -> list[TicketsByAgentItem]:
        return await self.repo.get_tickets_by_agent(db)

    async def get_tickets_by_type(self, db: AsyncSession) -> list[TicketsByTypeItem]:
        return await self.repo.get_tickets_by_type(db)

    async def get_summary(self, db: AsyncSession) -> DashboardSummary:
        return await self.repo.get_summary(db)
