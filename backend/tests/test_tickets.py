"""
Tests para /api/v1/tickets — CRUD de tickets, estados, tipos y mensajes.
"""

import pytest
from httpx import AsyncClient
from app.core.tenant import set_tenant_id


@pytest.mark.asyncio
async def test_crear_status(client: AsyncClient, auth_headers, tenant):
    set_tenant_id(tenant.id)
    resp = await client.post("/api/v1/tickets/statuses", headers=auth_headers, json={
        "name": "Abierto",
        "color": "#22C55E",
        "sort_order": 0,
        "is_default": True,
    })
    assert resp.status_code == 201
    assert resp.json()["name"] == "Abierto"


@pytest.mark.asyncio
async def test_listar_statuses(client: AsyncClient, auth_headers, default_status, tenant):
    set_tenant_id(tenant.id)
    resp = await client.get("/api/v1/tickets/statuses", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_crear_ticket(
    client: AsyncClient, auth_headers, customer, default_status, tenant
):
    set_tenant_id(tenant.id)
    resp = await client.post("/api/v1/tickets", headers=auth_headers, json={
        "subject": "Problema con factura",
        "customer_id": str(customer.id),
        "status_id": str(default_status.id),
        "priority": "high",
        "channel": "manual",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["subject"] == "Problema con factura"
    assert body["priority"] == "high"


@pytest.mark.asyncio
async def test_listar_tickets(
    client: AsyncClient, auth_headers, customer, default_status, tenant
):
    set_tenant_id(tenant.id)
    # Crear primero
    await client.post("/api/v1/tickets", headers=auth_headers, json={
        "subject": "Test ticket listado",
        "customer_id": str(customer.id),
        "status_id": str(default_status.id),
        "priority": "low",
        "channel": "manual",
    })
    resp = await client.get("/api/v1/tickets", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert body["total"] >= 1


@pytest.mark.asyncio
async def test_obtener_ticket_por_id(
    client: AsyncClient, auth_headers, customer, default_status, tenant
):
    set_tenant_id(tenant.id)
    created = await client.post("/api/v1/tickets", headers=auth_headers, json={
        "subject": "Ticket detalle",
        "customer_id": str(customer.id),
        "status_id": str(default_status.id),
        "priority": "medium",
        "channel": "manual",
    })
    ticket_id = created.json()["id"]

    resp = await client.get(f"/api/v1/tickets/{ticket_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == ticket_id


@pytest.mark.asyncio
async def test_ticket_inexistente_devuelve_404(
    client: AsyncClient, auth_headers, tenant
):
    set_tenant_id(tenant.id)
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = await client.get(f"/api/v1/tickets/{fake_id}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_actualizar_ticket(
    client: AsyncClient, auth_headers, admin_user, customer, default_status, tenant
):
    set_tenant_id(tenant.id)
    created = await client.post("/api/v1/tickets", headers=auth_headers, json={
        "subject": "Original",
        "customer_id": str(customer.id),
        "status_id": str(default_status.id),
        "priority": "low",
        "channel": "manual",
    })
    ticket_id = created.json()["id"]

    resp = await client.patch(f"/api/v1/tickets/{ticket_id}", headers=auth_headers, json={
        "priority": "urgent",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["priority"] == "urgent"
    assert body["updated_by"] == str(admin_user.id)
    assert body["last_activity"] is not None
    assert "Prioridad" in body["last_activity"]


@pytest.mark.asyncio
async def test_eliminar_ticket(
    client: AsyncClient, auth_headers, customer, default_status, tenant
):
    set_tenant_id(tenant.id)
    created = await client.post("/api/v1/tickets", headers=auth_headers, json={
        "subject": "Para eliminar",
        "customer_id": str(customer.id),
        "status_id": str(default_status.id),
        "priority": "low",
        "channel": "manual",
    })
    ticket_id = created.json()["id"]

    resp = await client.delete(f"/api/v1/tickets/{ticket_id}", headers=auth_headers)
    assert resp.status_code in (200, 204)


@pytest.mark.asyncio
async def test_crear_mensaje_en_ticket(
    client: AsyncClient, auth_headers, customer, default_status, tenant
):
    set_tenant_id(tenant.id)
    created = await client.post("/api/v1/tickets", headers=auth_headers, json={
        "subject": "Ticket con mensaje",
        "customer_id": str(customer.id),
        "status_id": str(default_status.id),
        "priority": "medium",
        "channel": "manual",
    })
    ticket_id = created.json()["id"]

    resp = await client.post(
        f"/api/v1/tickets/{ticket_id}/messages",
        headers=auth_headers,
        json={"body": "Hola, aquí va el mensaje"},
    )
    assert resp.status_code == 201
    assert resp.json()["body"] == "Hola, aquí va el mensaje"


@pytest.mark.asyncio
async def test_listar_mensajes_de_ticket(
    client: AsyncClient, auth_headers, customer, default_status, tenant
):
    set_tenant_id(tenant.id)
    created = await client.post("/api/v1/tickets", headers=auth_headers, json={
        "subject": "Ticket mensajes",
        "customer_id": str(customer.id),
        "status_id": str(default_status.id),
        "priority": "low",
        "channel": "manual",
    })
    ticket_id = created.json()["id"]

    await client.post(
        f"/api/v1/tickets/{ticket_id}/messages",
        headers=auth_headers,
        json={"body": "Mensaje uno"},
    )

    resp = await client.get(f"/api/v1/tickets/{ticket_id}/messages", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_ticket_sin_auth_devuelve_401(client: AsyncClient, tenant):
    resp = await client.get("/api/v1/tickets")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_actualizar_estado_ticket(
    client: AsyncClient, auth_headers, admin_user, customer, default_status, tenant
):
    set_tenant_id(tenant.id)
    # Crear un segundo estado para poder cambiar a él
    nuevo_status = await client.post("/api/v1/tickets/statuses", headers=auth_headers, json={
        "name": "En progreso",
        "color": "#3B82F6",
        "sort_order": 1,
        "is_default": False,
    })
    nuevo_status_id = nuevo_status.json()["id"]

    created = await client.post("/api/v1/tickets", headers=auth_headers, json={
        "subject": "Ticket cambio estado",
        "customer_id": str(customer.id),
        "status_id": str(default_status.id),
        "priority": "low",
        "channel": "manual",
    })
    ticket_id = created.json()["id"]

    resp = await client.patch(f"/api/v1/tickets/{ticket_id}", headers=auth_headers, json={
        "status_id": nuevo_status_id,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["status_id"] == nuevo_status_id
    assert body["updated_by"] == str(admin_user.id)
    assert body["last_activity"] is not None
    assert "Estado" in body["last_activity"]


@pytest.mark.asyncio
async def test_actualizar_agente_ticket(
    client: AsyncClient, auth_headers, admin_user, agent_user, customer, default_status, tenant
):
    set_tenant_id(tenant.id)
    created = await client.post("/api/v1/tickets", headers=auth_headers, json={
        "subject": "Ticket asignación agente",
        "customer_id": str(customer.id),
        "status_id": str(default_status.id),
        "priority": "medium",
        "channel": "manual",
    })
    ticket_id = created.json()["id"]

    resp = await client.patch(f"/api/v1/tickets/{ticket_id}", headers=auth_headers, json={
        "assigned_to": str(agent_user.id),
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["assigned_to"] == str(agent_user.id)
    assert body["updated_by"] == str(admin_user.id)
    assert body["last_activity"] is not None
    assert "asignado" in body["last_activity"].lower()


@pytest.mark.asyncio
async def test_reply_actualiza_actividad(
    client: AsyncClient, auth_headers, admin_user, customer, default_status, tenant
):
    set_tenant_id(tenant.id)
    created = await client.post("/api/v1/tickets", headers=auth_headers, json={
        "subject": "Ticket para reply",
        "customer_id": str(customer.id),
        "status_id": str(default_status.id),
        "priority": "low",
        "channel": "manual",
    })
    ticket_id = created.json()["id"]

    resp = await client.post(
        f"/api/v1/tickets/{ticket_id}/messages",
        headers=auth_headers,
        json={"body": "Respuesta de prueba", "msg_type": "reply"},
    )
    assert resp.status_code == 201

    ticket_resp = await client.get(f"/api/v1/tickets/{ticket_id}", headers=auth_headers)
    assert ticket_resp.status_code == 200
    body = ticket_resp.json()
    assert body["last_activity"] == "Respuesta enviada"
    assert body["updated_by"] == str(admin_user.id)
