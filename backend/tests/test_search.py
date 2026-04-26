"""
Tests para GET /api/v1/search — búsqueda global con FTS de PostgreSQL.

Estrategia de tests:
- Los triggers de tsvector NO se crean con create_all (solo con alembic upgrade).
  Por eso search_vector es NULL en crm_test y los tests cubren el fallback ILIKE.
- Toda la data se crea vía API (no db_session directamente en el test body)
  para evitar el conflicto greenlet de asyncpg que surge al mezclar
  db_session.commit() con el client de httpx en el mismo event loop.
- El endpoint usa `OR (search_vector @@ ts_query, col ILIKE '%q%')` así que
  ILIKE captura los registros con search_vector NULL.
"""

import pytest
from httpx import AsyncClient

from app.core.tenant import set_tenant_id


@pytest.mark.asyncio
async def test_search_tickets(
    client: AsyncClient,
    auth_headers: dict,
    tenant,
    default_status,
    customer,
):
    set_tenant_id(tenant.id)

    # Crear ticket con un subject que contenga la palabra buscada.
    r = await client.post(
        "/api/v1/tickets",
        headers=auth_headers,
        json={
            "subject": "Factura incorrecta de suscripción anual",
            "customer_id": str(customer.id),
            "status_id": str(default_status.id),
            "priority": "high",
            "channel": "manual",
        },
    )
    assert r.status_code == 201
    ticket_id = r.json()["id"]

    # search_vector es NULL → el fallback ILIKE encuentra el ticket por subject.
    resp = await client.get("/api/v1/search?q=factura", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["query"] == "factura"
    assert any(t["id"] == ticket_id for t in body["tickets"])
    assert body["total"] >= 1


@pytest.mark.asyncio
async def test_search_customers(
    client: AsyncClient,
    auth_headers: dict,
    tenant,
    customer,
):
    set_tenant_id(tenant.id)

    # customer fixture: full_name="Cliente Test" — ILIKE sobre full_name lo encuentra.
    resp = await client.get("/api/v1/search?q=Cliente", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert any(c["id"] == str(customer.id) for c in body["customers"])


@pytest.mark.asyncio
async def test_search_messages(
    client: AsyncClient,
    auth_headers: dict,
    tenant,
    default_status,
    customer,
):
    set_tenant_id(tenant.id)

    # Ticket contenedor.
    r_ticket = await client.post(
        "/api/v1/tickets",
        headers=auth_headers,
        json={
            "subject": "Soporte técnico general",
            "customer_id": str(customer.id),
            "status_id": str(default_status.id),
            "priority": "medium",
            "channel": "manual",
        },
    )
    assert r_ticket.status_code == 201
    ticket_id = r_ticket.json()["id"]
    ticket_number = r_ticket.json()["ticket_number"]

    # Mensaje con un término único buscable.
    r_msg = await client.post(
        f"/api/v1/tickets/{ticket_id}/messages",
        headers=auth_headers,
        json={"body": "Problemas de conexión al servidor de producción", "msg_type": "reply"},
    )
    assert r_msg.status_code == 201
    msg_id = r_msg.json()["id"]

    # search_vector es NULL → el fallback ILIKE sobre body encuentra el mensaje.
    resp = await client.get("/api/v1/search?q=servidor", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()

    results = body["messages"]
    assert any(m["id"] == msg_id for m in results)

    found = next(m for m in results if m["id"] == msg_id)
    assert found["ticket_id"] == ticket_id
    assert found["ticket_subject"] == "Soporte técnico general"
    assert "servidor" in found["body_snippet"].lower()


@pytest.mark.asyncio
async def test_search_query_corta(
    client: AsyncClient,
    auth_headers: dict,
    tenant,
):
    resp = await client.get("/api/v1/search?q=a", headers=auth_headers)
    assert resp.status_code == 400
    assert "2 caracteres" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_search_sin_resultados(
    client: AsyncClient,
    auth_headers: dict,
    tenant,
):
    resp = await client.get(
        "/api/v1/search?q=xyzzy_termino_inexistente_99",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["tickets"] == []
    assert body["customers"] == []
    assert body["messages"] == []
    assert body["total"] == 0


@pytest.mark.asyncio
async def test_search_sin_auth(client: AsyncClient, tenant):
    resp = await client.get("/api/v1/search?q=prueba")
    assert resp.status_code == 401
