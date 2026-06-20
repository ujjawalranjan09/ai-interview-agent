"""Auth endpoint tests."""

import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_register_and_login(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "securepass123", "full_name": "Test User", "role": "interviewer"},
    )
    assert resp.status_code == 201
    tokens = resp.json()
    assert "access_token" in tokens

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "test@example.com"

    login = await client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "securepass123"})
    assert login.status_code == 200


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await client.post("/api/v1/auth/register", json={"email": "dup@example.com", "password": "pass12345", "full_name": "Dup"})
    resp = await client.post("/api/v1/auth/register", json={"email": "dup@example.com", "password": "pass67890", "full_name": "Dup2"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    resp = await client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "wrongpass"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_unauthorized(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_register_validation_error(client):
    resp = await client.post("/api/v1/auth/register", json={"email": "bad", "password": "12", "full_name": ""})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_token_refresh(client):
    resp = await client.post("/api/v1/auth/register", json={"email": "test@example.com", "password": "securepass123", "full_name": "Test"})
    tokens = resp.json()
    refresh = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh.status_code == 200
    assert "access_token" in refresh.json()


@pytest.mark.asyncio
async def test_token_refresh_invalid(client):
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": "bad-token"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_update_profile(client, auth_headers):
    resp = await client.put("/api/v1/auth/me", json={"full_name": "Updated Name"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Updated Name"
