# backend/app/api/v1/auth.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.core.security import decode_token
from app.core.middleware import get_current_user
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserMe,
)
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Endpoints ─────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Ruta pública — valida credenciales y emite tokens."""
    service = AuthService(db)
    return await service.login(body.email, body.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Ruta pública — renueva el access token con el refresh token."""
    service = AuthService(db)
    return await service.refresh(body.refresh_token)


@router.get("/me", response_model=UserMe)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """Ruta protegida — devuelve el usuario autenticado."""
    return current_user