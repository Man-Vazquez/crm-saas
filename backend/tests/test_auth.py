"""
Tests para /api/v1/auth — login, refresh, y /me.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_exitoso(client: AsyncClient, admin_user, tenant):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "admin@test.com",
        "password": "Admin1234!",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_password_incorrecto(client: AsyncClient, admin_user, tenant):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "admin@test.com",
        "password": "WrongPass!",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_email_inexistente(client: AsyncClient, tenant):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "noexiste@test.com",
        "password": "cualquier",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_valido(client: AsyncClient, admin_user, tenant):
    login = await client.post("/api/v1/auth/login", json={
        "email": "admin@test.com",
        "password": "Admin1234!",
    })
    refresh_token = login.json()["refresh_token"]

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_refresh_token_invalido(client: AsyncClient, tenant):
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": "token.falso.aqui"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_autenticado(client: AsyncClient, admin_user, auth_headers, tenant):
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "admin@test.com"
    assert body["role"] == "admin"


@pytest.mark.asyncio
async def test_me_sin_token(client: AsyncClient, tenant):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code in (401, 403)
