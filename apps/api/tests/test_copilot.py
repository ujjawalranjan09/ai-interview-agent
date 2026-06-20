"""Copilot endpoint tests."""

import pytest


@pytest.mark.asyncio
async def test_start_copilot(client, auth_headers, interview_fixture):
    resp = await client.post(f"/api/v1/interviews/{interview_fixture['id']}/copilot/start", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_start_copilot_unauthorized(client, interview_fixture):
    resp = await client.post(f"/api/v1/interviews/{interview_fixture['id']}/copilot/start")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_suggestions(client, auth_headers, interview_fixture):
    await client.post(f"/api/v1/interviews/{interview_fixture['id']}/copilot/start", headers=auth_headers)
    resp = await client.get(f"/api/v1/interviews/{interview_fixture['id']}/copilot/suggestions", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_dismiss_suggestion(client, auth_headers, interview_fixture):
    await client.post(f"/api/v1/interviews/{interview_fixture['id']}/copilot/start", headers=auth_headers)
    resp = await client.get(f"/api/v1/interviews/{interview_fixture['id']}/copilot/suggestions", headers=auth_headers)
    suggestions = resp.json().get("suggestions", [])
    if suggestions:
        resp2 = await client.post(f"/api/v1/interviews/{interview_fixture['id']}/copilot/dismiss/{suggestions[0]['id']}", headers=auth_headers)
        assert resp2.status_code == 200
