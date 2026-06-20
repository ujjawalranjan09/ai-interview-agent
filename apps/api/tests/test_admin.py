"""Admin endpoint tests."""

import pytest


@pytest.mark.asyncio
async def test_list_users(client, admin_headers):
    resp = await client.get("/api/v1/admin/users", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_admin_non_admin_forbidden(client, auth_headers):
    resp = await client.get("/api/v1/admin/users", headers=auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_user_role(client, admin_headers):
    users = await client.get("/api/v1/admin/users", headers=admin_headers)
    items = users.json()["items"]
    if items:
        target = items[0]
        resp = await client.patch(f"/api/v1/admin/users/{target['id']}", json={"role": "candidate"}, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["role"] == "candidate"


@pytest.mark.asyncio
async def test_system_health(client, admin_headers):
    resp = await client.get("/api/v1/admin/system/health", headers=admin_headers)
    assert resp.status_code == 200
    assert "status" in resp.json()


@pytest.mark.asyncio
async def test_system_stats(client, admin_headers):
    resp = await client.get("/api/v1/admin/system/stats", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_users" in data
    assert "total_interviews" in data
