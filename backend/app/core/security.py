# backend/app/core/security.py

from datetime import datetime, timedelta, timezone
from uuid import UUID
from typing import Any

from jose import jwt
import bcrypt

from app.core.config import settings


# ── Hashing de contraseñas ────────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """Convierte una contraseña en texto plano a un hash bcrypt."""
    pwd_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica que una contraseña coincida con su hash bcrypt."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ── Creación de tokens JWT ────────────────────────────────────────────

def create_access_token(user_id: UUID, tenant_id: UUID, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {
        "sub":       str(user_id),
        "tenant_id": str(tenant_id),
        "role":      role,
        "exp":       expire,
        "type":      "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: UUID, tenant_id: UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload: dict[str, Any] = {
        "sub":       str(user_id),
        "tenant_id": str(tenant_id),
        "exp":       expire,
        "type":      "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )