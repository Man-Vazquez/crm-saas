from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, case, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import get_tenant_id
from app.models.ticket import Ticket
from app.models.ticket_config import TicketStatus, TicketType, TicketSubtype
from app.models.user import User
from app.schemas.metrics import (
    TicketsByStatusItem,
    TicketsByPriorityItem,
    TicketsByChannelItem,
    TicketsByAgentItem,
    TicketsByTypeItem,
    DailyTicketsItem,
    DashboardSummary,
)


class MetricsRepository:

    @property
    def tenant_id(self):
        return get_tenant_id()

    async def get_tickets_by_status(self, db: AsyncSession) -> list[TicketsByStatusItem]:
        rows = await db.execute(
            select(
                TicketStatus.name.label("status_name"),
                TicketStatus.color.label("color"),
                func.count(Ticket.id).label("count"),
            )
            .join(Ticket, Ticket.status_id == TicketStatus.id)
            .where(
                Ticket.tenant_id == self.tenant_id,
                Ticket.is_active == True,
                TicketStatus.tenant_id == self.tenant_id,
            )
            .group_by(TicketStatus.id, TicketStatus.name, TicketStatus.color)
            .order_by(func.count(Ticket.id).desc())
        )
        return [
            TicketsByStatusItem(status_name=r.status_name, color=r.color, count=r.count)
            for r in rows
        ]

    async def get_tickets_by_priority(self, db: AsyncSession) -> list[TicketsByPriorityItem]:
        rows = await db.execute(
            select(
                Ticket.priority.label("priority"),
                func.count(Ticket.id).label("count"),
            )
            .where(
                Ticket.tenant_id == self.tenant_id,
                Ticket.is_active == True,
            )
            .group_by(Ticket.priority)
            .order_by(func.count(Ticket.id).desc())
        )
        return [
            TicketsByPriorityItem(priority=r.priority, count=r.count)
            for r in rows
        ]

    async def get_tickets_by_channel(self, db: AsyncSession) -> list[TicketsByChannelItem]:
        rows = await db.execute(
            select(
                Ticket.channel.label("channel"),
                func.count(Ticket.id).label("count"),
            )
            .where(
                Ticket.tenant_id == self.tenant_id,
                Ticket.is_active == True,
            )
            .group_by(Ticket.channel)
            .order_by(func.count(Ticket.id).desc())
        )
        return [
            TicketsByChannelItem(channel=r.channel, count=r.count)
            for r in rows
        ]

    async def get_average_resolution_time(self, db: AsyncSession) -> float | None:
        result = await db.execute(
            select(
                func.avg(
                    extract("epoch", Ticket.resolved_at - Ticket.created_at) / 3600
                ).label("avg_hours")
            )
            .where(
                Ticket.tenant_id == self.tenant_id,
                Ticket.is_active == True,
                Ticket.resolved_at.is_not(None),
            )
        )
        value = result.scalar_one_or_none()
        return round(float(value), 2) if value is not None else None

    async def get_tickets_created_last_30_days(self, db: AsyncSession) -> list[DailyTicketsItem]:
        since = datetime.now(timezone.utc) - timedelta(days=30)
        rows = await db.execute(
            select(
                func.date(Ticket.created_at).label("date"),
                func.count(Ticket.id).label("count"),
            )
            .where(
                Ticket.tenant_id == self.tenant_id,
                Ticket.is_active == True,
                Ticket.created_at >= since,
            )
            .group_by(func.date(Ticket.created_at))
            .order_by(func.date(Ticket.created_at).asc())
        )
        return [
            DailyTicketsItem(date=str(r.date), count=r.count)
            for r in rows
        ]

    async def get_tickets_by_agent(self, db: AsyncSession) -> list[TicketsByAgentItem]:
        # Resolved status names (heuristic: names containing "resuelto" or "cerrado")
        # We count based on whether resolved_at is set, which is the definitive resolved signal.
        rows = await db.execute(
            select(
                User.full_name.label("agent_name"),
                func.count(Ticket.id).label("total"),
                func.sum(
                    case((Ticket.resolved_at.is_(None), 1), else_=0)
                ).label("open"),
                func.sum(
                    case((Ticket.resolved_at.is_not(None), 1), else_=0)
                ).label("resolved"),
            )
            .join(User, User.id == Ticket.assigned_to)
            .where(
                Ticket.tenant_id == self.tenant_id,
                Ticket.is_active == True,
                User.tenant_id == self.tenant_id,
            )
            .group_by(User.id, User.full_name)
            .order_by(func.count(Ticket.id).desc())
        )
        return [
            TicketsByAgentItem(
                agent_name=r.agent_name,
                total=r.total,
                open=r.open,
                resolved=r.resolved,
            )
            for r in rows
        ]

    async def get_tickets_by_type(self, db: AsyncSession) -> list[TicketsByTypeItem]:
        rows = await db.execute(
            select(
                TicketType.name.label("type_name"),
                TicketSubtype.name.label("subtype_name"),
                func.count(Ticket.id).label("count"),
            )
            .join(TicketType, TicketType.id == Ticket.type_id)
            .outerjoin(TicketSubtype, TicketSubtype.id == Ticket.subtype_id)
            .where(
                Ticket.tenant_id == self.tenant_id,
                Ticket.is_active == True,
                Ticket.type_id.is_not(None),
                TicketType.tenant_id == self.tenant_id,
            )
            .group_by(TicketType.id, TicketType.name, TicketSubtype.id, TicketSubtype.name)
            .order_by(func.count(Ticket.id).desc())
        )
        return [
            TicketsByTypeItem(
                type_name=r.type_name,
                subtype_name=r.subtype_name,
                count=r.count,
            )
            for r in rows
        ]

    async def get_summary(self, db: AsyncSession) -> DashboardSummary:
        # Join status names to detect open/in_progress/resolved/closed by name.
        # Use resolved_at for the resolved count — it is the authoritative signal.
        # For open vs in_progress vs closed we rely on status name conventions.
        status_rows = await db.execute(
            select(
                TicketStatus.name.label("status_name"),
                func.count(Ticket.id).label("count"),
            )
            .join(Ticket, Ticket.status_id == TicketStatus.id)
            .where(
                Ticket.tenant_id == self.tenant_id,
                Ticket.is_active == True,
                TicketStatus.tenant_id == self.tenant_id,
            )
            .group_by(TicketStatus.id, TicketStatus.name)
        )

        counts: dict[str, int] = {r.status_name.lower(): r.count for r in status_rows}

        def _match(keywords: list[str]) -> int:
            return sum(v for k, v in counts.items() if any(kw in k for kw in keywords))

        total_open = _match(["abierto", "nuevo", "open", "new"])
        total_in_progress = _match(["progreso", "proceso", "progress", "curso", "asignado"])
        total_resolved = _match(["resuelto", "resolved"])
        total_closed = _match(["cerrado", "closed"])

        avg_hours = await self.get_average_resolution_time(db)

        return DashboardSummary(
            total_open=total_open,
            total_in_progress=total_in_progress,
            total_resolved=total_resolved,
            total_closed=total_closed,
            avg_resolution_hours=avg_hours,
        )
