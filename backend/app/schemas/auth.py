from pydantic import BaseModel, EmailStr
from uuid import UUID


# ── Request schemas (lo que recibe la API) ────────────────────────────

class LoginRequest(BaseModel):
    """Cuerpo del POST /auth/login"""
    email: EmailStr        # Pydantic valida que sea un email válido
    password: str


class RefreshRequest(BaseModel):
    """Cuerpo del POST /auth/refresh"""
    refresh_token: str


# ── Response schemas (lo que devuelve la API) ─────────────────────────

class TokenResponse(BaseModel):
    """Respuesta exitosa del login y del refresh"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """
    Representa el payload decodificado de un JWT.
    Lo usamos internamente para tipar el resultado de decode_token().
    """
    sub: UUID           # user_id
    tenant_id: UUID
    role: str | None = None
    type: str           # "access" o "refresh"


class UserMe(BaseModel):
    """
    Información del usuario autenticado.
    Respuesta del GET /auth/me
    """
    id: UUID
    email: str
    full_name: str
    role: str
    tenant_id: UUID

    model_config = {"from_attributes": True}  # permite crear desde objetos ORM