"""
Tests para /api/v1/admin — gestión de usuarios y tenant.
"""

import pytest
from httpx import AsyncClient
from app.core.security import create_access_token
from app.core.tenant import set_tenant_id
from app.models.user import UserRole


@pytest.fixture
async def agent_headers(tenant, agent_user) -> dict:
    token = create_access_token(
        user_id=agent_user.id,
        tenant_id=tenant.id,
        role=agent_user.role.value,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_listar_usuarios(client: AsyncClient, auth_headers, admin_user, tenant):
    set_tenant_id(tenant.id)
    resp = await client.get("/api/v1/admin/users", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body
    assert body["total"] >= 1
    assert len(body["items"]) >= 1


@pytest.mark.asyncio
async def test_crear_usuario(client: AsyncClient, auth_headers, tenant):
    set_tenant_id(tenant.id)
    resp = await client.post("/api/v1/admin/users", headers=auth_headers, json={
        "email": "nuevo@test.com",
        "full_name": "Nuevo Agente",
        "password": "Pass1234!",
        "role": "agent",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "nuevo@test.com"
    assert body["role"] == "agent"


@pytest.mark.asyncio
async def test_crear_usuario_email_duplicado_devuelve_409(
    client: AsyncClient, auth_headers, admin_user, tenant
):
    set_tenant_id(tenant.id)
    resp = await client.post("/api/v1/admin/users", headers=auth_headers, json={
        "email": "admin@test.com",  # ya existe
        "full_name": "Duplicado",
        "password": "Pass1234!",
        "role": "agent",
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_agente_no_puede_listar_usuarios(
    client: AsyncClient, agent_user, tenant, agent_headers
):
    set_tenant_id(tenant.id)
    resp = await client.get("/api/v1/admin/users", headers=agent_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_actualizar_usuario(
    client: AsyncClient, auth_headers, agent_user, tenant
):
    set_tenant_id(tenant.id)
    resp = await client.patch(
        f"/api/v1/admin/users/{agent_user.id}",
        headers=auth_headers,
        json={"full_name": "Agente Renombrado"},
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Agente Renombrado"


@pytest.mark.asyncio
async def test_no_puede_eliminarse_a_si_mismo(
    client: AsyncClient, auth_headers, admin_user, tenant
):
    set_tenant_id(tenant.id)
    resp = await client.delete(
        f"/api/v1/admin/users/{admin_user.id}",
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_obtener_tenant(client: AsyncClient, auth_headers, tenant):
    set_tenant_id(tenant.id)
    resp = await client.get("/api/v1/admin/tenant", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["slug"] == "empresa-test"
    assert body["name"] == "Empresa Test"


@pytest.mark.asyncio
async def test_actualizar_tenant(client: AsyncClient, auth_headers, tenant):
    set_tenant_id(tenant.id)
    resp = await client.patch("/api/v1/admin/tenant", headers=auth_headers, json={
        "name": "Empresa Actualizada",
    })
    assert resp.status_code == 200
    assert resp.json()["name"] == "Empresa Actualizada"
