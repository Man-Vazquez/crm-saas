"""
Tests para /api/v1/customers — CRUD de clientes.
"""

import pytest
from httpx import AsyncClient
from app.core.tenant import set_tenant_id


@pytest.mark.asyncio
async def test_crear_cliente(client: AsyncClient, auth_headers, tenant):
    set_tenant_id(tenant.id)
    resp = await client.post("/api/v1/customers", headers=auth_headers, json={
        "full_name": "Juan Pérez",
        "email": "juan@empresa.com",
        "phone": "+521234567890",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["full_name"] == "Juan Pérez"
    assert body["email"] == "juan@empresa.com"


@pytest.mark.asyncio
async def test_listar_clientes(client: AsyncClient, auth_headers, customer, tenant):
    set_tenant_id(tenant.id)
    resp = await client.get("/api/v1/customers", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert body["total"] >= 1


@pytest.mark.asyncio
async def test_buscar_cliente_por_nombre(client: AsyncClient, auth_headers, customer, tenant):
    set_tenant_id(tenant.id)
    resp = await client.get("/api/v1/customers?search=Cliente", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any("Cliente" in c["full_name"] for c in items)


@pytest.mark.asyncio
async def test_obtener_cliente_por_id(client: AsyncClient, auth_headers, customer, tenant):
    set_tenant_id(tenant.id)
    resp = await client.get(f"/api/v1/customers/{customer.id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == str(customer.id)


@pytest.mark.asyncio
async def test_cliente_inexistente_devuelve_404(client: AsyncClient, auth_headers, tenant):
    set_tenant_id(tenant.id)
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = await client.get(f"/api/v1/customers/{fake_id}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_actualizar_cliente(client: AsyncClient, auth_headers, customer, tenant):
    set_tenant_id(tenant.id)
    resp = await client.patch(f"/api/v1/customers/{customer.id}", headers=auth_headers, json={
        "full_name": "Juan Modificado",
        "company": "Acme S.A.",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["full_name"] == "Juan Modificado"
    assert body["company"] == "Acme S.A."


@pytest.mark.asyncio
async def test_eliminar_cliente(client: AsyncClient, auth_headers, customer, tenant):
    set_tenant_id(tenant.id)
    resp = await client.delete(f"/api/v1/customers/{customer.id}", headers=auth_headers)
    assert resp.status_code in (200, 204)
