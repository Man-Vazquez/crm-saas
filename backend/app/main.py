from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.middleware import TenantMiddleware
from app.api.v1 import auth

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    # La documentación solo está disponible fuera de producción
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# ── Middlewares ───────────────────────────────────────────────────────
# El orden importa: CORS antes que Tenant.
# CORS necesita responder antes de que el Tenant intente leer el JWT.

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TenantMiddleware)

# ── Routers ───────────────────────────────────────────────────────────
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)

# En fases futuras:
# app.include_router(tickets.router, prefix=settings.API_V1_PREFIX)
# app.include_router(customers.router, prefix=settings.API_V1_PREFIX)


# ── Health check ──────────────────────────────────────────────────────
# Ruta pública que Docker y los servicios de monitoreo usan
# para verificar que la app está viva.
@app.get("/health")
async def health():
    return {"status": "ok", "environment": settings.ENVIRONMENT}