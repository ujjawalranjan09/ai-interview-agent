"""Interview endpoint tests."""

import pytest


@pytest.mark.asyncio
async def test_create_interview(client, auth_headers, candidate_fixture):
    resp = await client.post("/api/v1/interviews", json={"candidate_id": candidate_fixture["id"], "question_count": 3}, headers=auth_headers)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_list_interviews(client, auth_headers, interview_fixture):
    resp = await client.get("/api/v1/interviews", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_get_interview(client, auth_headers, interview_fixture):
    resp = await client.get(f"/api/v1/interviews/{interview_fixture['id']}", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_start_interview(client, auth_headers, interview_fixture):
    resp = await client.post(f"/api/v1/interviews/{interview_fixture['id']}/start", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_close_interview(client, auth_headers, interview_fixture):
    await client.post(f"/api/v1/interviews/{interview_fixture['id']}/start", headers=auth_headers)
    resp = await client.post(f"/api/v1/interviews/{interview_fixture['id']}/close", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_delete_interview(client, auth_headers, interview_fixture):
    resp = await client.delete(f"/api/v1/interviews/{interview_fixture['id']}", headers=auth_headers)
    assert resp.status_code == 204
