"""
Tests para /api/v1/metrics — endpoints del dashboard y reportes.
"""

import pytest
from httpx import AsyncClient
from app.core.tenant import set_tenant_id


@pytest.mark.asyncio
async def test_summary_sin_datos(client: AsyncClient, auth_headers, tenant):
    set_tenant_id(tenant.id)
    resp = await client.get("/api/v1/metrics/summary", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "total_open" in body
    assert "total_in_progress" in body
    assert "total_resolved" in body
    assert body["total_open"] == 0


@pytest.mark.asyncio
async def test_by_status_retorna_lista(client: AsyncClient, auth_headers, default_status, tenant):
    set_tenant_id(tenant.id)
    resp = await client.get("/api/v1/metrics/by-status", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_by_priority_retorna_lista(client: AsyncClient, auth_headers, tenant):
    set_tenant_id(tenant.id)
    resp = await client.get("/api/v1/metrics/by-priority", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_by_channel_retorna_lista(client: AsyncClient, auth_headers, tenant):
    set_tenant_id(tenant.id)
    resp = await client.get("/api/v1/metrics/by-channel", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_by_agent_retorna_lista(client: AsyncClient, auth_headers, tenant):
    set_tenant_id(tenant.id)
    resp = await client.get("/api/v1/metrics/by-agent", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_by_type_retorna_lista(client: AsyncClient, auth_headers, tenant):
    set_tenant_id(tenant.id)
    resp = await client.get("/api/v1/metrics/by-type", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_daily_retorna_lista(client: AsyncClient, auth_headers, tenant):
    set_tenant_id(tenant.id)
    resp = await client.get("/api/v1/metrics/daily", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    # Cada item tiene date y count
    if data:
        assert "date" in data[0]
        assert "count" in data[0]


@pytest.mark.asyncio
async def test_metrics_sin_auth_devuelve_401(client: AsyncClient, tenant):
    resp = await client.get("/api/v1/metrics/summary")
    assert resp.status_code == 401
