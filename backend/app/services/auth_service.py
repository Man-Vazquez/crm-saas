from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from uuid import UUID

from app.models.user import User
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.schemas.auth import TokenResponse
from jose import JWTError


class AuthService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def login(self, email: str, password: str) -> TokenResponse:
        """
        Valida credenciales y retorna los tokens.

        Nota: el mensaje de error es genérico intencionalmente.
        "Email o contraseña incorrectos" en lugar de "Email no encontrado"
        evita que un atacante descubra qué emails existen en el sistema.
        """
        # Buscar usuario por email — sin filtro de tenant porque
        # el login no tiene tenant todavía (es la ruta pública)
        result = await self.db.execute(
            select(User).where(
                User.email == email,
                User.is_active == True,
            )
        )
        user = result.scalar_one_or_none()

        # Mensaje genérico tanto si no existe el usuario
        # como si la contraseña es incorrecta
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
            )

        # Generar ambos tokens con el tenant_id del usuario
        access_token = create_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            role=user.role.value,
        )
        refresh_token = create_refresh_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """
        Valida el refresh token y emite un nuevo access token.
        """
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido o expirado",
            )

        # Verificar que sea un refresh token, no un access token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )

        user_id = UUID(payload["sub"])
        tenant_id = UUID(payload["tenant_id"])

        # Verificar que el usuario siga activo
        result = await self.db.execute(
            select(User).where(
                User.id == user_id,
                User.is_active == True,
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado o inactivo",
            )

        # Emitir tokens nuevos — rotación de refresh token
        # Cada refresh emite un nuevo refresh token también,
        # invalidando el anterior de facto
        new_access = create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            role=user.role.value,
        )
        new_refresh = create_refresh_token(
            user_id=user_id,
            tenant_id=tenant_id,
        )

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
        )