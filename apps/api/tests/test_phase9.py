"""Tests for Phase 9 features: Screening, Slack, Teams, Calendar, ATS, i18n, Email."""

from httpx import AsyncClient


class TestScreening:
    async def test_screen_requires_auth(self, client: AsyncClient):
        resp = await client.post("/api/v1/screening/candidates/00000000-0000-0000-0000-000000000000",
                                 json={"job_description": "x" * 50})
        assert resp.status_code == 401

    async def test_screen_candidate(self, client: AsyncClient, auth_headers: dict, candidate_fixture: dict):
        resp = await client.post(
            f"/api/v1/screening/candidates/{candidate_fixture['id']}",
            json={"job_description": "We are looking for a Python developer with strong skills in Python, SQL, and AWS. Must have experience with Docker and Kubernetes."},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "score" in data
        assert "recommendation" in data
        assert "strengths" in data
        assert "gaps" in data

    async def test_screen_candidate_not_found(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/api/v1/screening/candidates/00000000-0000-0000-0000-000000000000",
            json={"job_description": "x" * 50},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_rank_candidates(self, client: AsyncClient, auth_headers: dict, candidate_fixture: dict):
        resp = await client.post(
            "/api/v1/screening/rank",
            json={"job_description": "x" * 50, "candidate_ids": [candidate_fixture["id"]]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_screening_history(self, client: AsyncClient, auth_headers: dict, candidate_fixture: dict):
        resp = await client.get(
            f"/api/v1/screening/candidates/{candidate_fixture['id']}/history",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestSlackIntegration:
    async def test_list_slack_empty(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/integrations/slack", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_connect_slack(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/api/v1/integrations/slack",
            json={"webhook_url": "https://hooks.slack.com/test", "channel_name": "#test", "events": ["interview.completed"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["channel_name"] == "#test"

    async def test_delete_slack_not_found(self, client: AsyncClient, auth_headers: dict):
        resp = await client.delete(
            "/api/v1/integrations/slack/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestTeamsIntegration:
    async def test_list_teams_empty(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/integrations/teams", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_connect_teams(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/api/v1/integrations/teams",
            json={"webhook_url": "https://outlook.office.com/webhook/test", "channel_name": "General", "events": ["interview.completed"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True

    async def test_delete_teams_not_found(self, client: AsyncClient, auth_headers: dict):
        resp = await client.delete(
            "/api/v1/integrations/teams/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestATSIntegration:
    async def test_connect_ats_no_org(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/api/v1/integrations/ats",
            json={"provider": "greenhouse", "config": {"api_key": "test"}},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 400)

    async def test_list_ats(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/integrations/ats", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestDevEmailPreview:
    async def test_email_preview_list(self, client: AsyncClient):
        resp = await client.get("/api/v1/dev/email-preview/interview_invitation")
        assert resp.status_code in (200, 404)

    async def test_email_preview_unknown(self, client: AsyncClient):
        resp = await client.get("/api/v1/dev/email-preview/unknown_template")
        assert resp.status_code in (200, 404)


class TestI18n:
    async def test_get_translation(self):
        from app.core.i18n import get_translation
        result = get_translation("errors.not_found", "en")
        assert result == "Resource not found"

    async def test_get_translation_fallback(self):
        from app.core.i18n import get_translation
        result = get_translation("nonexistent.key", "en")
        assert result == "nonexistent.key"

    async def test_email_templates_list(self):
        from app.services.email_templates import list_templates
        templates = list_templates()
        assert "interview_invitation" in templates
        assert "welcome" in templates
        assert len(templates) == 7

    async def test_render_template(self):
        from app.services.email_templates import render_template
        subject, html, text = render_template("welcome", {"candidate_name": "Jane", "company_name": "Acme", "action_url": "https://example.com"})
        assert "Welcome" in subject
        assert "Jane" in html
