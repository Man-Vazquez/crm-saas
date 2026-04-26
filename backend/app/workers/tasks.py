import asyncio
import logging
import re
import uuid

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Subject cleaning
# ---------------------------------------------------------------------------

# Prefixes to strip (case-insensitive), followed by ':' and optional spaces.
_PREFIX_RE = re.compile(
    r'^(?:Re|Rr|RV|Fwd|FW|Ру|SV|AW|TR|回复|转发)\s*:\s*',
    re.IGNORECASE,
)


def _clean_subject(subject: str) -> str:
    """Strip common reply/forward prefixes from an email subject, repeatedly."""
    while True:
        stripped = _PREFIX_RE.sub('', subject).strip()
        if stripped == subject:
            return subject
        subject = stripped


def _extract_email_address(raw: str) -> str:
    """Return the bare email address from 'Name <addr>' or 'addr' strings."""
    if '<' in raw and '>' in raw:
        return raw.split('<')[1].split('>')[0].strip()
    return raw.strip()


def _extract_display_name(raw: str) -> str:
    """Return a human-readable name from a raw From header, falling back to the address."""
    if '<' in raw:
        name = raw.split('<')[0].strip().strip('"').strip("'")
        return name if name else _extract_email_address(raw)
    return _extract_email_address(raw)


# ---------------------------------------------------------------------------
# Core async email processing
# ---------------------------------------------------------------------------

async def _process_email(payload: dict, channel_id: str, tenant_id: str) -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select

    from app.core.config import settings
    from app.models.channel import Channel
    from app.models.customer import Customer
    from app.models.ticket import Ticket
    from app.models.ticket_config import TicketStatus
    from app.models.message import Message

    tenant_uuid = uuid.UUID(tenant_id)
    channel_uuid = uuid.UUID(channel_id)

    from_raw = payload.get("from", "")
    from_email = _extract_email_address(from_raw)
    from_name = _extract_display_name(from_raw)
    raw_subject = payload.get("subject", "")
    cleaned_subject = _clean_subject(raw_subject) or raw_subject or "(sin asunto)"
    in_reply_to = payload.get("in_reply_to")
    message_id = payload.get("message_id", "")
    body      = payload.get("body") or payload.get("text") or ""
    body_html = payload.get("body_html")  # None para emails solo texto plano

    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            async with session.begin():

                # ── 0. Resolve channel → department_id ─────────────────────
                result = await session.execute(
                    select(Channel).where(Channel.id == channel_uuid)
                )
                channel_obj = result.scalar_one_or_none()
                department_id = channel_obj.department_id if channel_obj else None

                # ── 1. Find or create customer ──────────────────────────────
                result = await session.execute(
                    select(Customer).where(
                        Customer.email == from_email,
                        Customer.tenant_id == tenant_uuid,
                    )
                )
                customer = result.scalar_one_or_none()

                if customer is None:
                    customer = Customer(
                        tenant_id=tenant_uuid,
                        full_name=from_name,
                        email=from_email,
                    )
                    session.add(customer)
                    await session.flush()
                    logger.info(f"Cliente creado: {from_email} (tenant={tenant_id})")

                # ── 2. Find existing ticket ─────────────────────────────────
                ticket = None

                # 2a. In-Reply-To: look for a message whose metadata.external_id matches
                if in_reply_to:
                    result = await session.execute(
                        select(Message).where(
                            Message.tenant_id == tenant_uuid,
                            Message.metadata_["external_id"].astext == in_reply_to,
                        ).limit(1)
                    )
                    ref_message = result.scalar_one_or_none()
                    if ref_message is not None:
                        result = await session.execute(
                            select(Ticket).where(
                                Ticket.id == ref_message.ticket_id,
                                Ticket.is_active == True,
                            )
                        )
                        ticket = result.scalar_one_or_none()
                        if ticket:
                            logger.info(
                                f"Ticket encontrado por In-Reply-To: {ticket.id}"
                            )

                # 2b. Cleaned subject match on the same channel
                if ticket is None:
                    result = await session.execute(
                        select(Ticket).where(
                            Ticket.tenant_id == tenant_uuid,
                            Ticket.subject == cleaned_subject,
                            Ticket.channel_id == channel_uuid,
                            Ticket.is_active == True,
                        ).order_by(Ticket.created_at.desc()).limit(1)
                    )
                    ticket = result.scalar_one_or_none()
                    if ticket:
                        logger.info(
                            f"Ticket encontrado por asunto '{cleaned_subject}': {ticket.id}"
                        )

                # ── 3. Create new ticket if no match ────────────────────────
                if ticket is None:
                    # Resolve default status for this tenant
                    result = await session.execute(
                        select(TicketStatus).where(
                            TicketStatus.tenant_id == tenant_uuid,
                            TicketStatus.is_default == True,
                            TicketStatus.is_active == True,
                        )
                    )
                    status = result.scalar_one_or_none()

                    if status is None:
                        result = await session.execute(
                            select(TicketStatus).where(
                                TicketStatus.tenant_id == tenant_uuid,
                                TicketStatus.is_active == True,
                            ).order_by(TicketStatus.sort_order).limit(1)
                        )
                        status = result.scalar_one_or_none()

                    if status is None:
                        logger.error(
                            f"No hay estados de ticket configurados para tenant {tenant_id}. "
                            "Email descartado."
                        )
                        return

                    ticket = Ticket(
                        tenant_id=tenant_uuid,
                        customer_id=customer.id,
                        status_id=status.id,
                        subject=cleaned_subject,
                        channel="email",
                        channel_id=channel_uuid,
                        priority="medium",
                        department_id=department_id,
                    )
                    session.add(ticket)
                    await session.flush()
                    logger.info(
                        f"Ticket creado: '{cleaned_subject}' (tenant={tenant_id})"
                    )

                # ── 4. Dedup: skip si el external_id ya fue procesado ──────────────
                # Verificación explícita antes del INSERT; el índice único parcial
                # uq_messages_tenant_external_id es el safety net ante race conditions.
                if message_id:
                    result = await session.execute(
                        select(Message).where(
                            Message.tenant_id == tenant_uuid,
                            Message.external_id == message_id,
                        ).limit(1)
                    )
                    if result.scalar_one_or_none() is not None:
                        logger.warning(
                            f"Email ya procesado, ignorando duplicado | "
                            f"external_id={message_id} | tenant={tenant_id}"
                        )
                        return

                # ── 5. Create inbound message ───────────────────────────────
                message = Message(
                    tenant_id=tenant_uuid,
                    ticket_id=ticket.id,
                    author_id=None,
                    body=body,
                    body_html=body_html,
                    direction="inbound",
                    msg_type="reply",
                    external_id=message_id or None,
                    metadata_={
                        "external_id": message_id,
                        "from": from_raw,
                    },
                )
                session.add(message)
                await session.flush()
                logger.info(
                    f"Mensaje inbound guardado | ticket={ticket.id} | from={from_email}"
                )

    finally:
        await engine.dispose()


# ---------------------------------------------------------------------------
# Celery tasks
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def process_incoming_message(
    self,
    payload: dict,
    channel_id: str,
    channel_type: str,
    tenant_id: str,
):
    try:
        logger.info(
            f"Procesando mensaje entrante | canal={channel_type} | tenant={tenant_id}"
        )
        if channel_type == "email":
            asyncio.run(_process_email(payload, channel_id, tenant_id))
        else:
            logger.warning(f"Tipo de canal no soportado aún: {channel_type}")
        return {"status": "ok", "channel": channel_type}
    except Exception as exc:
        logger.error(f"Error procesando mensaje: {exc}", exc_info=True)
        raise self.retry(exc=exc)


@celery_app.task
def send_outbound_message(
    ticket_id: str,
    message_body: str,
    channel_type: str,
    tenant_id: str,
):
    logger.info(f"Enviando mensaje | ticket={ticket_id} | canal={channel_type}")
    return {"status": "queued", "ticket_id": ticket_id}


@celery_app.task(name="poll_email_channels")
def poll_email_channels():
    """
    Tarea periódica: revisa el IMAP de todos los canales de email activos
    y encola los mensajes nuevos para procesamiento.
    Se ejecuta cada 60 segundos via Celery Beat.
    """
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select
    from app.models.channel import Channel
    from app.channels.email import EmailChannel
    from app.core.config import settings

    logger.info("Iniciando polling de canales email...")

    async def _poll():
        engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            result = await session.execute(
                select(Channel).where(
                    Channel.channel_type == "email",
                    Channel.is_active == True,
                )
            )
            channels = result.scalars().all()
            logger.info(f"Canales email activos: {len(channels)}")

            for channel in channels:
                try:
                    adapter = EmailChannel(config=channel.config)
                    emails = adapter.fetch_unread_emails()

                    for inbound_msg in emails:
                        process_incoming_message.delay(
                            payload=inbound_msg.raw_payload,
                            channel_id=str(channel.id),
                            channel_type="email",
                            tenant_id=str(channel.tenant_id),
                        )
                        logger.info(f"Email encolado: {inbound_msg.from_address}")

                except Exception as e:
                    logger.error(f"Error polling canal {channel.id}: {e}")
                    continue

        await engine.dispose()

    asyncio.run(_poll())
