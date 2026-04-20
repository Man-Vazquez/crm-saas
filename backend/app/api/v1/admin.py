from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.core.database import get_db
from app.core.middleware import get_current_user
from app.core.security import hash_password
from app.core.tenant import get_tenant_id
from app.models.user import User, UserRole
from app.models.tenant import Tenant

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Dependencies ──────────────────────────────────────────────────────────────

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.ADMIN, UserRole.SUPERVISOR):
        raise HTTPException(status_code=403, detail="Se requiere rol admin o supervisor")
    return current_user


async def require_admin_write(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Se requiere rol admin")
    return current_user


# ── Schemas (inline — admin-only, no need for a separate schemas file) ────────

class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.AGENT


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class TenantResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    plan: str
    is_active: bool

    model_config = {"from_attributes": True}


class TenantUpdate(BaseModel):
    name: str


# ── User endpoints ────────────────────────────────────────────────────────────

@router.get("/users", response_model=dict)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    tenant_id = get_tenant_id()
    total = (await db.execute(
        select(func.count(User.id)).where(User.tenant_id == tenant_id)
    )).scalar_one()
    items = (await db.execute(
        select(User)
        .where(User.tenant_id == tenant_id)
        .order_by(User.full_name)
        .offset(skip)
        .limit(limit)
    )).scalars().all()
    return {
        "items": [UserResponse.model_validate(u) for u in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_write),
):
    tenant_id = get_tenant_id()

    existing = await db.execute(
        select(User).where(User.email == data.email, User.tenant_id == tenant_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409, detail="Ya existe un usuario con ese email en este tenant"
        )

    user = User(
        tenant_id=tenant_id,
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_write),
):
    result = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == get_tenant_id())
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    await db.flush()
    await db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_write),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")

    result = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == get_tenant_id())
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user.is_active = False
    await db.flush()


# ── Tenant endpoints ──────────────────────────────────────────────────────────

@router.get("/tenant", response_model=TenantResponse)
async def get_tenant(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_write),
):
    result = await db.execute(
        select(Tenant).where(Tenant.id == get_tenant_id())
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    return tenant


@router.patch("/tenant", response_model=TenantResponse)
async def update_tenant(
    data: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin_write),
):
    result = await db.execute(
        select(Tenant).where(Tenant.id == get_tenant_id())
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    tenant.name = data.name
    await db.flush()
    await db.refresh(tenant)
    return tenant
