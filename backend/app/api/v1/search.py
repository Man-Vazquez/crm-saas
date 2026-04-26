# backend/app/api/v1/search.py

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, or_, select, nullslast

from app.core.database import get_db
from app.core.middleware import get_current_user
from app.core.tenant import get_tenant_id
from app.models.user import User
from app.models.ticket import Ticket
from app.models.ticket_config import TicketStatus
from app.models.customer import Customer
from app.models.message import Message

router = APIRouter(prefix="/search", tags=["search"])


# ── Query helpers ──────────────────────────────────────────────────────────


async def _search_tickets(
    db: AsyncSession,
    tenant_id,
    q: str,
    ts_query,
    limit: int,
) -> list[dict]:
    stmt = (
        select(
            Ticket,
            TicketStatus.name.label("status_name"),
            Customer.full_name.label("customer_name"),
        )
        .join(TicketStatus, Ticket.status_id == TicketStatus.id)
        .join(Customer, Ticket.customer_id == Customer.id)
        .where(
            Ticket.tenant_id == tenant_id,
            Ticket.is_active == True,
            or_(
                Ticket.search_vector.op("@@")(ts_query),
                Ticket.subject.ilike(f"%{q}%"),
            ),
        )
        .order_by(nullslast(func.ts_rank(Ticket.search_vector, ts_query).desc()))
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        {
            "id": str(row.Ticket.id),
            "ticket_number": row.Ticket.ticket_number,
            "subject": row.Ticket.subject,
            "status": row.status_name,
            "priority": row.Ticket.priority,
            "channel": row.Ticket.channel,
            "customer_name": row.customer_name,
        }
        for row in rows
    ]


async def _search_customers(
    db: AsyncSession,
    tenant_id,
    q: str,
    ts_query,
    limit: int,
) -> list[dict]:
    stmt = (
        select(Customer)
        .where(
            Customer.tenant_id == tenant_id,
            Customer.is_active == True,
            or_(
                Customer.search_vector.op("@@")(ts_query),
                Customer.full_name.ilike(f"%{q}%"),
                Customer.email.ilike(f"%{q}%"),
                Customer.company.ilike(f"%{q}%"),
            ),
        )
        .order_by(nullslast(func.ts_rank(Customer.search_vector, ts_query).desc()))
        .limit(limit)
    )
    result = await db.execute(stmt)
    customers = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "name": c.full_name,
            "email": c.email,
            "company": c.company,
        }
        for c in customers
    ]


async def _search_messages(
    db: AsyncSession,
    tenant_id,
    q: str,
    ts_query,
    limit: int,
) -> list[dict]:
    stmt = (
        select(
            Message,
            Ticket.ticket_number.label("ticket_number"),
            Ticket.subject.label("ticket_subject"),
        )
        .join(Ticket, Message.ticket_id == Ticket.id)
        .where(
            Message.tenant_id == tenant_id,
            Message.msg_type != "comment",
            or_(
                Message.search_vector.op("@@")(ts_query),
                Message.body.ilike(f"%{q}%"),
            ),
        )
        .order_by(nullslast(func.ts_rank(Message.search_vector, ts_query).desc()))
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        {
            "id": str(row.Message.id),
            "ticket_id": str(row.Message.ticket_id),
            "ticket_number": row.ticket_number,
            "ticket_subject": row.ticket_subject,
            "body_snippet": (row.Message.body or "")[:150],
        }
        for row in rows
    ]


# ── Endpoint ───────────────────────────────────────────────────────────────


@router.get("")
async def search(
    q: str = Query(...),
    limit: int = Query(default=5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Búsqueda global por tickets, clientes y mensajes.

    Usa full-text search de PostgreSQL (tsvector/tsquery) con fallback ILIKE
    para registros sin search_vector indexado. Las tres queries comparten la misma
    sesión y corren secuencialmente — asyncio.gather no es seguro con asyncpg sobre
    una sesión compartida (causa InterfaceError: another operation is in progress).
    """
    if len(q) < 2:
        raise HTTPException(
            status_code=400,
            detail="La búsqueda requiere al menos 2 caracteres.",
        )

    tenant_id = get_tenant_id()
    ts_query  = func.plainto_tsquery("spanish", q)

    tickets   = await _search_tickets(db, tenant_id, q, ts_query, limit)
    customers = await _search_customers(db, tenant_id, q, ts_query, limit)
    messages  = await _search_messages(db, tenant_id, q, ts_query, limit)

    return {
        "query": q,
        "tickets": tickets,
        "customers": customers,
        "messages": messages,
        "total": len(tickets) + len(customers) + len(messages),
    }
