"""Async interview (join) endpoint tests."""

import pytest


@pytest.mark.asyncio
async def test_share_interview(client, auth_headers, interview_fixture):
    resp = await client.post(f"/api/v1/interviews/{interview_fixture['id']}/share", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "share_token" in data
    assert "share_url" in data


@pytest.mark.asyncio
async def test_share_reuse_token(client, auth_headers, interview_fixture):
    r1 = await client.post(f"/api/v1/interviews/{interview_fixture['id']}/share", headers=auth_headers)
    t1 = r1.json()["share_token"]
    r2 = await client.post(f"/api/v1/interviews/{interview_fixture['id']}/share", headers=auth_headers)
    assert r2.json()["share_token"] == t1


@pytest.mark.asyncio
async def test_join_invalid_token(client):
    resp = await client.get("/api/v1/interviews/join/invalid")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_submit_join_answer_wrong_question(client, auth_headers, interview_fixture):
    share = await client.post(f"/api/v1/interviews/{interview_fixture['id']}/share", headers=auth_headers)
    token = share.json()["share_token"]
    resp = await client.post(
        f"/api/v1/interviews/join/{token}/answer",
        json={"question_id": "00000000-0000-0000-0000-000000000000", "answer_text": "Test answer"},
    )
    assert resp.status_code == 403
