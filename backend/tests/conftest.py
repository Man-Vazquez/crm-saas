"""
conftest.py — Fixtures compartidas para toda la suite de tests.

Estrategia de aislamiento:
- Base de datos separada: crm_test (misma instancia de Postgres).
- get_db se sobreescribe con app.dependency_overrides para que todos los
  endpoints usen la sesión de test.
- Cada test empieza con un TRUNCATE tenants CASCADE (elimina en cascada
  todas las filas relacionadas).
- Los tipos de enum (user_role, plan_type) se crean con IF NOT EXISTS
  antes de create_all, porque los modelos usan create_type=False.
"""

import re
import pytest
import pytest_asyncio
from uuid import UUID
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.core.tenant import set_tenant_id
from app.main import app
from app.models.tenant import Tenant, PlanType
from app.models.user import User, UserRole
from app.models.customer import Customer
from app.models.ticket_config import TicketStatus

# ── URL de la base de datos de test ──────────────────────────────────
# Reemplaza el nombre de la DB al final de la URL por crm_test
TEST_DATABASE_URL = re.sub(
    r"/([^/?]+)(\?.*)?$",
    r"/crm_test\2",
    settings.DATABASE_URL,
)

# NullPool: cada sesión abre su propia conexión sin pool.
# Esto evita el conflicto de greenlets cuando BaseHTTPMiddleware crea
# un nuevo task de asyncio y asyncpg intenta reutilizar una conexión
# que fue creada en un contexto diferente.
engine_test = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
TestingSessionLocal = async_sessionmaker(
    engine_test, expire_on_commit=False, class_=AsyncSession
)


# ── Crear tablas (una sola vez por sesión de pytest) ──────────────────
@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with engine_test.begin() as conn:
        # Drop all tables so schema changes (new columns, etc.) are always reflected.
        # ENUMs are not tracked by metadata (create_type=False) so they survive.
        await conn.run_sync(Base.metadata.drop_all)
        # Los enums con create_type=False requieren existir antes de create_all.
        # asyncpg no soporta CREATE TYPE IF NOT EXISTS — usamos DO $$ BEGIN ... EXCEPTION.
        await conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE user_role AS ENUM ('admin', 'supervisor', 'agent');
            EXCEPTION WHEN duplicate_object THEN NULL;
            END $$;
        """))
        await conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE plan_type AS ENUM ('free', 'starter', 'growth', 'enterprise');
            EXCEPTION WHEN duplicate_object THEN NULL;
            END $$;
        """))
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine_test.dispose()


# ── Limpiar datos entre tests ─────────────────────────────────────────
@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    yield
    async with engine_test.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE tenants CASCADE"))


# ── Sesión de DB para tests ───────────────────────────────────────────
@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    async with TestingSessionLocal() as session:
        yield session


# ── Sobreescribir get_db en el app ────────────────────────────────────
# La app recibe su PROPIA sesión por request — no comparte la db_session
# del fixture. Esto evita conflictos de greenlet con BaseHTTPMiddleware.
@pytest_asyncio.fixture
async def client() -> AsyncClient:
    async def _get_test_db():
        async with TestingSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _get_test_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Fixtures de datos ─────────────────────────────────────────────────

@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession) -> Tenant:
    t = Tenant(
        name="Empresa Test",
        slug="empresa-test",
        plan=PlanType.STARTER,
        is_active=True,
    )
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession, tenant: Tenant) -> User:
    u = User(
        tenant_id=tenant.id,
        email="admin@test.com",
        hashed_password=hash_password("Admin1234!"),
        full_name="Admin Test",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def agent_user(db_session: AsyncSession, tenant: Tenant) -> User:
    u = User(
        tenant_id=tenant.id,
        email="agente@test.com",
        hashed_password=hash_password("Agent1234!"),
        full_name="Agente Test",
        role=UserRole.AGENT,
        is_active=True,
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def auth_headers(tenant: Tenant, admin_user: User) -> dict:
    token = create_access_token(
        user_id=admin_user.id,
        tenant_id=tenant.id,
        role=admin_user.role.value,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def default_status(db_session: AsyncSession, tenant: Tenant) -> TicketStatus:
    s = TicketStatus(
        tenant_id=tenant.id,
        name="Abierto",
        color="#22C55E",
        sort_order=0,
        is_default=True,
        is_active=True,
    )
    db_session.add(s)
    await db_session.commit()
    await db_session.refresh(s)
    return s


@pytest_asyncio.fixture
async def customer(db_session: AsyncSession, tenant: Tenant) -> Customer:
    c = Customer(
        tenant_id=tenant.id,
        full_name="Cliente Test",
        email="cliente@test.com",
        phone="+521234567890",
        is_active=True,
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    return c
