# backend/app/api/v1/auth.py

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
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

# Limiter definido aquí para que main.py pueda importarlo sin circular imports.
# storage_uri apunta a Redis para que los contadores sean compartidos entre workers.
# swallow_errors=True: si Redis no está disponible, los errores se absorben y la
# solicitud pasa (la app sigue funcionando sin rate limiting como fallback).
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,
    swallow_errors=True,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _exempt_in_development() -> bool:
    """Excluye el rate limiting en desarrollo para no afectar tests ni CI."""
    return settings.ENVIRONMENT == "development"


# ── Endpoints ─────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute", exempt_when=_exempt_in_development)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Ruta pública — valida credenciales y emite tokens."""
    service = AuthService(db)
    return await service.login(body.email, body.password)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute", exempt_when=_exempt_in_development)
async def refresh(
    request: Request,
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