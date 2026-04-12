from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

from app.core.config import settings


# ── Engine ────────────────────────────────────────────────────────────
# Se crea una vez. Gestiona el pool de conexiones a PostgreSQL.
#
# pool_pre_ping=True: antes de usar una conexión del pool, SQLAlchemy
# hace un SELECT 1 para verificar que sigue viva. Sin esto, si PostgreSQL
# reinicia, el pool tiene conexiones "muertas" y los queries fallan.
#
# pool_size=10: conexiones permanentes en el pool.
# max_overflow=20: conexiones adicionales permitidas bajo carga alta.
# Esto significa máximo 30 conexiones simultáneas a PostgreSQL.
# Ajusta según el plan de tu servidor de base de datos.
engine: AsyncEngine = create_async_engine(
    str(settings.DATABASE_URL),
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.is_development,  # imprime SQL en consola solo en desarrollo
)


# ── Session factory ───────────────────────────────────────────────────
# Fábrica que crea sessions. No es una session en sí misma.
#
# expire_on_commit=False: por defecto SQLAlchemy "expira" los objetos
# después de un commit, forzando un nuevo SELECT si accedes a sus atributos.
# En un contexto async esto causa errores porque la session ya cerró.
# Con False, los objetos conservan sus valores después del commit.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Base para modelos ─────────────────────────────────────────────────
# Todos los modelos SQLAlchemy heredan de esta clase.
# DeclarativeBase registra los modelos y les da acceso a la metadata
# que Alembic necesita para generar migraciones.
class Base(DeclarativeBase):
    pass


# ── Dependencia de FastAPI ────────────────────────────────────────────
# Esta función es la pieza más importante de este archivo.
# FastAPI la llama antes de cada request y le inyecta la session al handler.
#
# El patrón "yield" convierte esto en un context manager:
# - el código ANTES del yield se ejecuta antes del handler
# - el código DESPUÉS del yield se ejecuta después (en el finally)
# Esto garantiza que la session SIEMPRE se cierre, incluso si hay excepciones.
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()      # si todo salió bien, confirma los cambios
        except Exception:
            await session.rollback()    # si algo falló, revierte todo
            raise                       # re-lanza la excepción para que FastAPI la maneje