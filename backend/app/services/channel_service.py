from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.channel import Channel
from app.models.ticket import Ticket
from app.models.customer import Customer
from app.models.message import Message
from app.channels.email import EmailChannel
from app.channels.base import OutboundMessage
from app.core.tenant import get_tenant_id
from app.core.encryption import decrypt_config
import logging

logger = logging.getLogger(__name__)


class ChannelService:

    async def reply_to_ticket(
        self,
        db: AsyncSession,
        ticket_id: UUID,
        agent_id: UUID,
        body: str,
    ) -> Message:
        tenant_id = get_tenant_id()

        # 1. Obtener ticket
        ticket_result = await db.execute(
            select(Ticket).where(
                and_(Ticket.id == ticket_id, Ticket.tenant_id == tenant_id)
            )
        )
        ticket = ticket_result.scalar_one_or_none()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket no encontrado")

        # 2. Obtener canal
        channel = None
        if ticket.channel_id:
            ch_result = await db.execute(
                select(Channel).where(
                    and_(Channel.id == ticket.channel_id, Channel.tenant_id == tenant_id)
                )
            )
            channel = ch_result.scalar_one_or_none()

        if not channel:
            ch_result = await db.execute(
                select(Channel).where(
                    and_(
                        Channel.tenant_id == tenant_id,
                        Channel.channel_type == ticket.channel,
                        Channel.is_active == True,
                    )
                )
            )
            channel = ch_result.scalars().first()

        if not channel:
            raise HTTPException(
                status_code=400,
                detail=f"No hay canal activo configurado para '{ticket.channel}'"
            )

        # 3. Obtener cliente
        cust_result = await db.execute(
            select(Customer).where(
                and_(Customer.id == ticket.customer_id, Customer.tenant_id == tenant_id)
            )
        )
        customer = cust_result.scalar_one_or_none()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        # 4. Enviar por canal
        sent = await self._send_by_channel(channel, customer, ticket, body)
        if not sent:
            raise HTTPException(status_code=500, detail="Error enviando el mensaje por el canal")

        # 5. Guardar mensaje en DB
        message = Message(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            author_id=agent_id,
            body=body,
            direction="outbound",
            msg_type="reply",
            metadata={"channel_id": str(channel.id), "channel_type": channel.channel_type},
        )
        db.add(message)
        await db.flush()
        await db.refresh(message)

        logger.info(f"Respuesta enviada | ticket={ticket_id} | canal={channel.channel_type}")
        return message

    async def _send_by_channel(self, channel, customer, ticket, body: str) -> bool:
        if channel.channel_type == "email":
            if not customer.email:
                raise HTTPException(status_code=400, detail="El cliente no tiene email registrado")
            adapter = EmailChannel(config=channel.config)
            message = OutboundMessage(
                to_address=customer.email,
                body=body,
                subject=f"Re: {ticket.subject}",
                reply_to_external_id=None,
            )
            return await adapter.send(message)

        raise HTTPException(
            status_code=400,
            detail=f"Tipo de canal '{channel.channel_type}' no soportado aún"
        )