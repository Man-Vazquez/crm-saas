"""
Tests para /api/v1/departments — gestión de departamentos y sus agentes.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.core.tenant import set_tenant_id
from app.models.department import Department
from app.models.tenant import Tenant, PlanType
from app.models.user import User, UserRole


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
async def agent_headers(tenant, agent_user) -> dict:
    token = create_access_token(
        user_id=agent_user.id,
        tenant_id=tenant.id,
        role=agent_user.role.value,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def other_tenant_user(db_session: AsyncSession) -> User:
    """Usuario perteneciente a un segundo tenant distinto al tenant de test."""
    t2 = Tenant(name="Otro Tenant", slug="otro-tenant", plan=PlanType.STARTER, is_active=True)
    db_session.add(t2)
    await db_session.commit()
    await db_session.refresh(t2)

    u2 = User(
        tenant_id=t2.id,
        email="externo@otro.com",
        hashed_password=hash_password("Pass1234!"),
        full_name="Externo",
        role=UserRole.AGENT,
        is_active=True,
    )
    db_session.add(u2)
    await db_session.commit()
    await db_session.refresh(u2)
    return u2


@pytest_asyncio.fixture
async def other_tenant_dept(db_session: AsyncSession) -> Department:
    """Departamento perteneciente a un segundo tenant distinto al tenant de test."""
    t2 = Tenant(name="Tenant Dos", slug="tenant-dos", plan=PlanType.STARTER, is_active=True)
    db_session.add(t2)
    await db_session.commit()
    await db_session.refresh(t2)

    dept = Department(tenant_id=t2.id, name="Dept Tenant 2", is_active=True)
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)
    return dept


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_crear_departamento(client: AsyncClient, auth_headers, tenant):
    set_tenant_id(tenant.id)
    resp = await client.post("/api/v1/departments", headers=auth_headers, json={
        "name": "Soporte Técnico",
        "description": "Atiende incidencias técnicas",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Soporte Técnico"
    assert body["description"] == "Atiende incidencias técnicas"
    assert body["is_active"] is True
    assert body["agent_count"] == 0
    assert body["channel_count"] == 0


@pytest.mark.asyncio
async def test_listar_departamentos(client: AsyncClient, auth_headers, tenant):
    set_tenant_id(tenant.id)
    await client.post("/api/v1/departments", headers=auth_headers, json={"name": "Ventas"})
    await client.post("/api/v1/departments", headers=auth_headers, json={"name": "TI"})

    resp = await client.get("/api/v1/departments", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 2
    names = {i["name"] for i in items}
    assert names == {"Ventas", "TI"}
    # Cada item tiene agent_count y channel_count
    for item in items:
        assert "agent_count" in item
        assert "channel_count" in item


@pytest.mark.asyncio
async def test_editar_departamento(client: AsyncClient, auth_headers, tenant):
    set_tenant_id(tenant.id)
    create_resp = await client.post(
        "/api/v1/departments", headers=auth_headers, json={"name": "Original"}
    )
    dept_id = create_resp.json()["id"]

    patch_resp = await client.patch(
        f"/api/v1/departments/{dept_id}",
        headers=auth_headers,
        json={"name": "Renombrado", "description": "Nueva descripción"},
    )
    assert patch_resp.status_code == 200
    body = patch_resp.json()
    assert body["name"] == "Renombrado"
    assert body["description"] == "Nueva descripción"


@pytest.mark.asyncio
async def test_soft_delete_departamento(client: AsyncClient, auth_headers, tenant):
    set_tenant_id(tenant.id)
    create_resp = await client.post(
        "/api/v1/departments", headers=auth_headers, json={"name": "A Eliminar"}
    )
    dept_id = create_resp.json()["id"]

    del_resp = await client.delete(
        f"/api/v1/departments/{dept_id}", headers=auth_headers
    )
    assert del_resp.status_code == 204

    # No debe aparecer en el listado
    list_resp = await client.get("/api/v1/departments", headers=auth_headers)
    ids = [i["id"] for i in list_resp.json()]
    assert dept_id not in ids


@pytest.mark.asyncio
async def test_agregar_agente(client: AsyncClient, auth_headers, agent_user, tenant):
    set_tenant_id(tenant.id)
    dept_resp = await client.post(
        "/api/v1/departments", headers=auth_headers, json={"name": "TI"}
    )
    dept_id = dept_resp.json()["id"]

    add_resp = await client.post(
        f"/api/v1/departments/{dept_id}/agents",
        headers=auth_headers,
        json={"user_id": str(agent_user.id)},
    )
    assert add_resp.status_code == 204

    # agent_count debe reflejarse en el listado
    get_resp = await client.get(f"/api/v1/departments/{dept_id}", headers=auth_headers)
    assert get_resp.json()["agent_count"] == 1


@pytest.mark.asyncio
async def test_listar_agentes(client: AsyncClient, auth_headers, agent_user, tenant):
    set_tenant_id(tenant.id)
    dept_resp = await client.post(
        "/api/v1/departments", headers=auth_headers, json={"name": "Ventas"}
    )
    dept_id = dept_resp.json()["id"]

    await client.post(
        f"/api/v1/departments/{dept_id}/agents",
        headers=auth_headers,
        json={"user_id": str(agent_user.id)},
    )

    list_resp = await client.get(
        f"/api/v1/departments/{dept_id}/agents", headers=auth_headers
    )
    assert list_resp.status_code == 200
    agents = list_resp.json()
    assert len(agents) == 1
    assert agents[0]["email"] == agent_user.email
    assert agents[0]["full_name"] == agent_user.full_name


@pytest.mark.asyncio
async def test_quitar_agente(client: AsyncClient, auth_headers, agent_user, tenant):
    set_tenant_id(tenant.id)
    dept_resp = await client.post(
        "/api/v1/departments", headers=auth_headers, json={"name": "Soporte"}
    )
    dept_id = dept_resp.json()["id"]

    await client.post(
        f"/api/v1/departments/{dept_id}/agents",
        headers=auth_headers,
        json={"user_id": str(agent_user.id)},
    )

    del_resp = await client.delete(
        f"/api/v1/departments/{dept_id}/agents/{agent_user.id}",
        headers=auth_headers,
    )
    assert del_resp.status_code == 204

    agents_resp = await client.get(
        f"/api/v1/departments/{dept_id}/agents", headers=auth_headers
    )
    assert agents_resp.json() == []


@pytest.mark.asyncio
async def test_agente_otro_tenant_rechazado(
    client: AsyncClient, auth_headers, tenant, other_tenant_user: User
):
    """Intentar agregar un usuario de otro tenant → 400.

    Los datos del segundo tenant se crean en el fixture other_tenant_user
    (antes del test), por lo que el cuerpo del test solo hace llamadas HTTP.
    """
    set_tenant_id(tenant.id)

    dept_resp = await client.post(
        "/api/v1/departments", headers=auth_headers, json={"name": "TI"}
    )
    assert dept_resp.status_code == 201
    dept_id = dept_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/departments/{dept_id}/agents",
        headers=auth_headers,
        json={"user_id": str(other_tenant_user.id)},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_departamento_sin_auth(client: AsyncClient):
    """Sin token → 401."""
    resp = await client.get("/api/v1/departments")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_departamento_otro_tenant(
    client: AsyncClient, tenant, auth_headers, other_tenant_dept: Department
):
    """Un admin no puede ver ni editar departamentos de otro tenant → 404.

    El departamento del segundo tenant se crea en el fixture other_tenant_dept
    (antes del test), por lo que el cuerpo del test solo hace llamadas HTTP.
    """
    set_tenant_id(tenant.id)

    resp = await client.patch(
        f"/api/v1/departments/{other_tenant_dept.id}",
        headers=auth_headers,
        json={"name": "Intruso"},
    )
    assert resp.status_code == 404
