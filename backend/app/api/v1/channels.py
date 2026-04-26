from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.middleware import get_current_user
from app.core.tenant import get_tenant_id
from app.models.user import User
from app.repositories.channel_repo import ChannelRepository
from app.schemas.channel import (
    ChannelCreate, ChannelUpdate, ChannelResponse,
    AgentChannelCreate, AgentChannelResponse,
)

router = APIRouter(prefix="/channels", tags=["channels"])


def get_repo(tenant_id: UUID = Depends(get_tenant_id)) -> ChannelRepository:
    return ChannelRepository(tenant_id=tenant_id)


# ── Canales ────────────────────────────────────────────────────────────

@router.post("", response_model=ChannelResponse, status_code=201)
async def create_channel(
    data: ChannelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    repo: ChannelRepository = Depends(get_repo),
):
    """Crea un canal nuevo para el tenant. Solo admins."""
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden crear canales")
    return await repo.create(db, data.channel_type, data.name, data.config, data.department_id)


@router.get("", response_model=dict)
async def list_channels(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    repo: ChannelRepository = Depends(get_repo),
):
    """Lista todos los canales del tenant."""
    items, total = await repo.get_paginated(db, skip, limit)
    return {
        "items": [ChannelResponse.model_validate(c) for c in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    repo: ChannelRepository = Depends(get_repo),
):
    channel = await repo.get_by_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Canal no encontrado")
    return channel


@router.patch("/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: UUID,
    data: ChannelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    repo: ChannelRepository = Depends(get_repo),
):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden editar canales")
    channel = await repo.get_by_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Canal no encontrado")
    return await repo.update(db, channel, data.model_dump(exclude_unset=True))


@router.delete("/{channel_id}", status_code=204)
async def delete_channel(
    channel_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    repo: ChannelRepository = Depends(get_repo),
):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden eliminar canales")
    channel = await repo.get_by_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Canal no encontrado")
    await repo.delete(db, channel)


# ── Asignación de agentes ──────────────────────────────────────────────

@router.post("/{channel_id}/agents", response_model=AgentChannelResponse, status_code=201)
async def assign_agent_to_channel(
    channel_id: UUID,
    data: AgentChannelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    repo: ChannelRepository = Depends(get_repo),
):
    """Asigna un agente a un canal."""
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden asignar agentes")
    channel = await repo.get_by_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Canal no encontrado")
    try:
        return await repo.assign_agent(db, data.agent_id, channel_id)
    except Exception:
        raise HTTPException(status_code=409, detail="El agente ya está asignado a este canal")


@router.delete("/{channel_id}/agents/{agent_id}", status_code=204)
async def remove_agent_from_channel(
    channel_id: UUID,
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    repo: ChannelRepository = Depends(get_repo),
):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden remover agentes")
    removed = await repo.remove_agent(db, agent_id, channel_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")


@router.get("/{channel_id}/agents", response_model=list[AgentChannelResponse])
async def get_agents_for_channel(
    channel_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    repo: ChannelRepository = Depends(get_repo),
):
    """Lista los agentes asignados a un canal."""
    return await repo.get_agents_for_channel(db, channel_id)