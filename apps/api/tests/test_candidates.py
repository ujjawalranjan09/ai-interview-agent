"""Candidate endpoint tests."""

import pytest


@pytest.mark.asyncio
async def test_create_candidate(client, auth_headers):
    resp = await client.post("/api/v1/candidates", json={"name": "John", "email": "john@example.com"}, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["name"] == "John"


@pytest.mark.asyncio
async def test_list_candidates(client, auth_headers, candidate_fixture):
    resp = await client.get("/api/v1/candidates", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_candidate(client, auth_headers, candidate_fixture):
    resp = await client.get(f"/api/v1/candidates/{candidate_fixture['id']}", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_candidate_not_found(client, auth_headers):
    resp = await client.get("/api/v1/candidates/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_candidate(client, auth_headers, candidate_fixture):
    resp = await client.put(f"/api/v1/candidates/{candidate_fixture['id']}", json={"name": "Updated"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"
