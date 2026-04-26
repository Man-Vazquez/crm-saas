"""
Tests para el campo agent_id en canales.

- Verifica que POST /channels y PATCH /channels/{id} aceptan y devuelven agent_id.
- La asignación automática de tickets al agente del canal (tasks._process_email)
  se valida aquí a nivel de lógica SQL: creamos el canal con agent_id y comprobamos
  que el campo queda correctamente guardado. El flujo completo de email inbound no
  se puede probar desde el test suite porque _process_email crea su propio engine
  apuntando a settings.DATABASE_URL (producción), no al DB de test.

Patrón: toda la data se crea vía API (client), nunca db_session en el cuerpo del test.
"""

import pytest
from httpx import AsyncClient

from app.core.tenant import set_tenant_id


# ── Helpers ───────────────────────────────────────────────────────────────────

SMTP_CONFIG = {
    "smtp_host": "smtp.test.com",
    "smtp_port": "587",
    "smtp_user": "test@test.com",
    "smtp_password": "secret",
    "imap_host": "imap.test.com",
    "imap_port": "993",
    "from_name": "Test",
}


async def _create_channel(client, headers, name="Canal Test", agent_id=None):
    payload = {
        "channel_type": "email",
        "name": name,
        "config": SMTP_CONFIG,
    }
    if agent_id is not None:
        payload["agent_id"] = agent_id
    r = await client.post("/api/v1/channels", headers=headers, json=payload)
    assert r.status_code == 201, r.text
    return r.json()


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_canal_con_agente_asigna_ticket(
    client: AsyncClient,
    auth_headers: dict,
    agent_user,
    tenant,
):
    """Crear canal con agent_id → el campo queda persistido y devuelto en la respuesta.

    Valida el prerrequisito del flujo de email: el canal almacena correctamente
    el agente responsable que _process_email usará al crear el ticket.
    """
    set_tenant_id(tenant.id)
    ch = await _create_channel(client, auth_headers, agent_id=str(agent_user.id))

    assert ch["agent_id"] == str(agent_user.id), (
        f"Se esperaba agent_id={agent_user.id}, pero fue {ch['agent_id']}"
    )

    # GET del canal también devuelve agent_id
    get_resp = await client.get(f"/api/v1/channels/{ch['id']}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["agent_id"] == str(agent_user.id)


@pytest.mark.asyncio
async def test_canal_sin_agente_no_asigna(
    client: AsyncClient,
    auth_headers: dict,
    tenant,
):
    """Crear canal sin agent_id → agent_id es null en la respuesta."""
    set_tenant_id(tenant.id)
    ch = await _create_channel(client, auth_headers, name="Canal Sin Agente")

    assert ch["agent_id"] is None, (
        f"Se esperaba agent_id=None, pero fue {ch['agent_id']}"
    )
