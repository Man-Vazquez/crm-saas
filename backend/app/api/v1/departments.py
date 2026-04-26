from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.core.database import get_db
from app.core.middleware import get_current_user
from app.core.tenant import get_tenant_id
from app.models.user import User
from app.models.channel import Channel
from app.models.department import Department, DepartmentAgent
from app.schemas.department import (
    AgentAddRequest,
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
    DepartmentAgentResponse,
)

router = APIRouter(prefix="/departments", tags=["departments"])


# ── Dependencies ──────────────────────────────────────────────────────────────

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    from app.models.user import UserRole
    if current_user.role not in (UserRole.ADMIN, UserRole.SUPERVISOR):
        raise HTTPException(status_code=403, detail="Se requiere rol admin o supervisor")
    return current_user


async def require_admin_write(current_user: User = Depends(get_current_user)) -> User:
    from app.models.user import UserRole
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Se requiere rol admin")
    return current_user


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_department_or_404(dept_id: UUID, tenant_id, db: AsyncSession) -> Department:
    result = await db.execute(
        select(Department).where(
            Department.id == dept_id,
            Department.tenant_id == tenant_id,
        )
    )
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Departamento no encontrado")
    return dept


async def _build_response(dept: Department, db: AsyncSession) -> DepartmentResponse:
    agent_count = (await db.execute(
        select(func.count()).select_from(DepartmentAgent)
        .where(DepartmentAgent.department_id == dept.id)
    )).scalar_one()

    channel_count = (await db.execute(
        select(func.count()).select_from(Channel)
        .where(Channel.department_id == dept.id, Channel.tenant_id == dept.tenant_id)
    )).scalar_one()

    return DepartmentResponse(
        id=dept.id,
        tenant_id=dept.tenant_id,
        name=dept.name,
        description=dept.description,
        is_active=dept.is_active,
        created_at=dept.created_at,
        updated_at=dept.updated_at,
        agent_count=agent_count,
        channel_count=channel_count,
    )


# ── Endpoints: Department CRUD ────────────────────────────────────────────────

@router.get("", response_model=list[DepartmentResponse])
async def list_departments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = get_tenant_id()
    depts = (await db.execute(
        select(Department)
        .where(Department.tenant_id == tenant_id, Department.is_active == True)
        .order_by(Department.name)
    )).scalars().all()

    return [await _build_response(d, db) for d in depts]


@router.get("/{dept_id}", response_model=DepartmentResponse)
async def get_department(
    dept_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dept = await _get_department_or_404(dept_id, get_tenant_id(), db)
    return await _build_response(dept, db)


@router.post("", response_model=DepartmentResponse, status_code=201)
async def create_department(
    data: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_write),
):
    tenant_id = get_tenant_id()
    dept = Department(
        tenant_id=tenant_id,
        name=data.name,
        description=data.description,
    )
    db.add(dept)
    await db.flush()
    await db.refresh(dept)
    return await _build_response(dept, db)


@router.patch("/{dept_id}", response_model=DepartmentResponse)
async def update_department(
    dept_id: UUID,
    data: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_write),
):
    dept = await _get_department_or_404(dept_id, get_tenant_id(), db)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(dept, field, value)

    await db.flush()
    await db.refresh(dept)
    return await _build_response(dept, db)


@router.delete("/{dept_id}", status_code=204)
async def delete_department(
    dept_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_write),
):
    dept = await _get_department_or_404(dept_id, get_tenant_id(), db)
    dept.is_active = False
    await db.flush()


# ── Endpoints: Agents ─────────────────────────────────────────────────────────

@router.get("/{dept_id}/agents", response_model=list[DepartmentAgentResponse])
async def list_agents(
    dept_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_department_or_404(dept_id, get_tenant_id(), db)

    users = (await db.execute(
        select(User)
        .join(DepartmentAgent, DepartmentAgent.user_id == User.id)
        .where(DepartmentAgent.department_id == dept_id)
        .order_by(User.full_name)
    )).scalars().all()

    return [
        DepartmentAgentResponse(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role.value,
        )
        for u in users
    ]


@router.post("/{dept_id}/agents", status_code=204)
async def add_agent(
    dept_id: UUID,
    data: AgentAddRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_write),
):
    tenant_id = get_tenant_id()
    await _get_department_or_404(dept_id, tenant_id, db)

    # Verify the user belongs to the same tenant
    user = (await db.execute(
        select(User).where(User.id == data.user_id, User.tenant_id == tenant_id)
    )).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="El usuario no pertenece a este tenant")

    # Idempotent — ignore if already assigned
    existing = (await db.execute(
        select(DepartmentAgent).where(
            DepartmentAgent.department_id == dept_id,
            DepartmentAgent.user_id == data.user_id,
        )
    )).scalar_one_or_none()
    if existing:
        return

    db.add(DepartmentAgent(department_id=dept_id, user_id=data.user_id))
    await db.flush()


@router.delete("/{dept_id}/agents/{user_id}", status_code=204)
async def remove_agent(
    dept_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_write),
):
    await _get_department_or_404(dept_id, get_tenant_id(), db)

    row = (await db.execute(
        select(DepartmentAgent).where(
            DepartmentAgent.department_id == dept_id,
            DepartmentAgent.user_id == user_id,
        )
    )).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="El agente no está asignado a este departamento")

    await db.delete(row)
    await db.flush()
