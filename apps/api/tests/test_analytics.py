"""Analytics endpoint tests."""

import pytest


@pytest.mark.asyncio
async def test_overview(client, auth_headers):
    resp = await client.get("/api/v1/analytics/overview", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_interviews" in data
    assert "average_score" in data


@pytest.mark.asyncio
async def test_trends(client, auth_headers):
    resp = await client.get("/api/v1/analytics/trends", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "weekly_scores" in data
    assert "skill_distribution" in data
