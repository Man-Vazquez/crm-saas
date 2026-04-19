from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.middleware import get_current_user
from app.services.metrics_service import MetricsService
from app.schemas.metrics import (
    TicketsByStatusItem,
    TicketsByPriorityItem,
    TicketsByChannelItem,
    TicketsByAgentItem,
    TicketsByTypeItem,
    DailyTicketsItem,
    DashboardSummary,
)

router = APIRouter(prefix="/metrics", tags=["metrics"])


def get_service() -> MetricsService:
    return MetricsService()


@router.get("/summary", response_model=DashboardSummary)
async def summary(
    db: AsyncSession = Depends(get_db),
    _: object = Depends(get_current_user),
):
    return await get_service().get_summary(db)


@router.get("/by-status", response_model=list[TicketsByStatusItem])
async def by_status(
    db: AsyncSession = Depends(get_db),
    _: object = Depends(get_current_user),
):
    return await get_service().get_tickets_by_status(db)


@router.get("/by-priority", response_model=list[TicketsByPriorityItem])
async def by_priority(
    db: AsyncSession = Depends(get_db),
    _: object = Depends(get_current_user),
):
    return await get_service().get_tickets_by_priority(db)


@router.get("/by-channel", response_model=list[TicketsByChannelItem])
async def by_channel(
    db: AsyncSession = Depends(get_db),
    _: object = Depends(get_current_user),
):
    return await get_service().get_tickets_by_channel(db)


@router.get("/by-agent", response_model=list[TicketsByAgentItem])
async def by_agent(
    db: AsyncSession = Depends(get_db),
    _: object = Depends(get_current_user),
):
    return await get_service().get_tickets_by_agent(db)


@router.get("/by-type", response_model=list[TicketsByTypeItem])
async def by_type(
    db: AsyncSession = Depends(get_db),
    _: object = Depends(get_current_user),
):
    return await get_service().get_tickets_by_type(db)


@router.get("/daily", response_model=list[DailyTicketsItem])
async def daily(
    db: AsyncSession = Depends(get_db),
    _: object = Depends(get_current_user),
):
    return await get_service().get_tickets_created_last_30_days(db)
