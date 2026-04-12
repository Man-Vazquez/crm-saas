from uuid import UUID
from fastapi import Request, Response, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.tenant import set_tenant_id, get_tenant_id
from app.core.database import get_db

PUBLIC_PATHS = {
    "/health",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/docs",
    "/openapi.json",
    "/redoc",
}

bearer_scheme = HTTPBearer()


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Token de autenticación requerido"},
            )

        token = authorization.split(" ")[1]

        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )

            tenant_id_str = payload.get("tenant_id")
            if not tenant_id_str:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Token inválido: falta tenant_id"},
                )

            tenant_id = UUID(tenant_id_str)

        except JWTError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token inválido o expirado"},
            )
        except ValueError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token malformado"},
            )

        set_tenant_id(tenant_id)
        response = await call_next(request)
        return response


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    from app.models.user import User

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id_str = payload.get("sub")
        token_type = payload.get("type")

        if not user_id_str or token_type != "access":
            raise HTTPException(status_code=401, detail="Token inválido")

        user_id = UUID(user_id_str)

    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    return user