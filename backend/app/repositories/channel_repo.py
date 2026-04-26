from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, and_
from app.models.channel import Channel
from app.models.agent_channel import AgentChannel
from app.core.encryption import encrypt_config, decrypt_config


class ChannelRepository:

    def __init__(self, tenant_id: UUID):
        self.tenant_id = tenant_id

    # ── Canales ────────────────────────────────────────────────────

    async def create(
        self, db: AsyncSession, channel_type: str, name: str, config: dict,
        department_id: UUID | None = None,
    ) -> Channel:
        # Encriptar credenciales antes de guardar
        encrypted = encrypt_config(config)
        channel = Channel(
            tenant_id=self.tenant_id,
            channel_type=channel_type,
            name=name,
            config=encrypted,
            department_id=department_id,
        )
        db.add(channel)
        await db.flush()
        await db.refresh(channel)
        return channel

    async def get_all(self, db: AsyncSession) -> list[Channel]:
        result = await db.execute(
            select(Channel).where(Channel.tenant_id == self.tenant_id)
        )
        return result.scalars().all()

    async def get_paginated(
        self, db: AsyncSession, skip: int, limit: int
    ) -> tuple[list[Channel], int]:
        total = (await db.execute(
            select(func.count(Channel.id)).where(Channel.tenant_id == self.tenant_id)
        )).scalar_one()
        items = (await db.execute(
            select(Channel)
            .where(Channel.tenant_id == self.tenant_id)
            .order_by(Channel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )).scalars().all()
        return items, total

    async def get_by_id(self, db: AsyncSession, channel_id: UUID) -> Channel | None:
        result = await db.execute(
            select(Channel).where(
                and_(
                    Channel.id == channel_id,
                    Channel.tenant_id == self.tenant_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_active_by_type(self, db: AsyncSession, channel_type: str) -> list[Channel]:
        result = await db.execute(
            select(Channel).where(
                and_(
                    Channel.tenant_id == self.tenant_id,
                    Channel.channel_type == channel_type,
                    Channel.is_active == True,
                )
            )
        )
        return result.scalars().all()

    # Fields that may legitimately be set to None (nullable FKs)
    _NULLABLE_FIELDS = frozenset({"department_id"})

    async def update(self, db: AsyncSession, channel: Channel, data: dict) -> Channel:
        if "config" in data and data["config"]:
            data["config"] = encrypt_config(data["config"])
        for key, value in data.items():
            if value is not None or key in self._NULLABLE_FIELDS:
                setattr(channel, key, value)
        await db.flush()
        await db.refresh(channel)
        return channel

    async def delete(self, db: AsyncSession, channel: Channel) -> None:
        await db.delete(channel)
        await db.flush()

    # ── Asignación de agentes ──────────────────────────────────────

    async def assign_agent(self, db: AsyncSession, agent_id: UUID, channel_id: UUID) -> AgentChannel:
        assignment = AgentChannel(
            tenant_id=self.tenant_id,
            agent_id=agent_id,
            channel_id=channel_id,
        )
        db.add(assignment)
        await db.flush()
        await db.refresh(assignment)
        return assignment

    async def remove_agent(self, db: AsyncSession, agent_id: UUID, channel_id: UUID) -> bool:
        result = await db.execute(
            select(AgentChannel).where(
                and_(
                    AgentChannel.agent_id == agent_id,
                    AgentChannel.channel_id == channel_id,
                    AgentChannel.tenant_id == self.tenant_id,
                )
            )
        )
        assignment = result.scalar_one_or_none()
        if not assignment:
            return False
        await db.delete(assignment)
        await db.flush()
        return True

    async def get_agents_for_channel(self, db: AsyncSession, channel_id: UUID) -> list[AgentChannel]:
        result = await db.execute(
            select(AgentChannel).where(
                and_(
                    AgentChannel.channel_id == channel_id,
                    AgentChannel.tenant_id == self.tenant_id,
                )
            )
        )
        return result.scalars().all()

    async def get_channels_for_agent(self, db: AsyncSession, agent_id: UUID) -> list[AgentChannel]:
        result = await db.execute(
            select(AgentChannel).where(
                and_(
                    AgentChannel.agent_id == agent_id,
                    AgentChannel.tenant_id == self.tenant_id,
                )
            )
        )
        return result.scalars().all()