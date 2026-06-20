"""JD matching endpoint tests."""

import pytest


@pytest.mark.asyncio
async def test_match_jd(client, auth_headers, candidate_fixture):
    resp = await client.post(
        f"/api/v1/candidates/{candidate_fixture['id']}/jd",
        json={"jd_text": "We need a software engineer with Python and JavaScript skills. Required: Python. Preferred: React and AWS."},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "match_percentage" in data


@pytest.mark.asyncio
async def test_match_jd_too_short(client, auth_headers, candidate_fixture):
    resp = await client.post(
        f"/api/v1/candidates/{candidate_fixture['id']}/jd",
        json={"jd_text": "Too short"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_generate_jd_questions(client, auth_headers, candidate_fixture):
    resp = await client.post(
        f"/api/v1/candidates/{candidate_fixture['id']}/jd/questions",
        json={"jd_text": "We need a software engineer with Python and JavaScript skills. Required: Python. Preferred: React and AWS.", "count": 3},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "questions" in data
