"""Report, coaching, replay endpoint tests."""

import pytest


@pytest.mark.asyncio
async def test_get_report_not_found(client, auth_headers, interview_fixture):
    resp = await client.get(f"/api/v1/interviews/{interview_fixture['id']}/report", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_coaching_not_found(client, auth_headers, interview_fixture):
    resp = await client.get(f"/api/v1/interviews/{interview_fixture['id']}/coaching", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_replay_not_completed(client, auth_headers, interview_fixture):
    resp = await client.get(f"/api/v1/interviews/{interview_fixture['id']}/replay", headers=auth_headers)
    assert resp.status_code == 400
