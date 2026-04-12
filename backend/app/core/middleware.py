from uuid import UUID
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError

from app.core.config import settings
from app.core.tenant import set_tenant_id


# Rutas que no requieren autenticación ni tenant.
# El middleware las deja pasar sin validar el JWT.
PUBLIC_PATHS = {
    "/health",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/docs",          # Swagger UI
    "/openapi.json",  # schema de la API
    "/redoc",
}


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware que se ejecuta en CADA request antes de llegar al handler.

    Responsabilidades:
    1. Verificar que el JWT es válido
    2. Extraer el tenant_id del JWT
    3. Inyectarlo en el ContextVar para que los repositories lo usen
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # ── Rutas públicas ────────────────────────────────────────────
        # Las dejamos pasar sin validar nada.
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # ── Extraer el token del header ───────────────────────────────
        # El header debe ser: "Authorization: Bearer <token>"
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Token de autenticación requerido"},
            )

        token = authorization.split(" ")[1]  # extrae solo el token

        # ── Validar y decodificar el JWT ──────────────────────────────
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )

            # El JWT debe tener tenant_id en su payload.
            # Lo pusimos ahí al crear el token en el login (próxima pieza).
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

        # ── Inyectar el tenant en el contexto ─────────────────────────
        # A partir de aquí, cualquier código en este request
        # puede llamar get_tenant_id() y obtendrá este UUID.
        set_tenant_id(tenant_id)

        # ── Continuar con el request ──────────────────────────────────
        response = await call_next(request)
        return response