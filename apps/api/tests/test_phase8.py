"""Tests for Phase 8 features: Search, GDPR, Scheduling, Bulk, Proctoring, Plagiarism, Branding."""

import pytest
from httpx import AsyncClient


class TestSearch:
    async def test_search_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/search?q=test")
        assert resp.status_code == 401

    async def test_search_empty_query(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/search?q=", headers=auth_headers)
        assert resp.status_code == 422

    async def test_search_returns_results(self, client: AsyncClient, auth_headers: dict, candidate_fixture: dict):
        name = candidate_fixture["name"][:3]
        resp = await client.get(f"/api/v1/search?q={name}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "candidates" in data
        assert data["total"] >= 0

    async def test_search_by_type(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/search?q=test&type=candidates", headers=auth_headers)
        assert resp.status_code == 200
        assert "candidates" in resp.json()


class TestGDPR:
    async def test_list_consents(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/gdpr/consents", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_update_consent(self, client: AsyncClient, auth_headers: dict):
        resp = await client.put(
            "/api/v1/gdpr/consents",
            json={"consent_type": "marketing", "granted": True},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["granted"] is True

    async def test_toggle_consent_off(self, client: AsyncClient, auth_headers: dict):
        await client.put(
            "/api/v1/gdpr/consents",
            json={"consent_type": "marketing", "granted": True},
            headers=auth_headers,
        )
        resp = await client.put(
            "/api/v1/gdpr/consents",
            json={"consent_type": "marketing", "granted": False},
            headers=auth_headers,
        )
        assert resp.json()["granted"] is False

    async def test_request_data_export(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post("/api/v1/gdpr/export", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "pending"

    async def test_export_status(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/gdpr/export", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_delete_data(self, client: AsyncClient, auth_headers: dict):
        resp = await client.delete("/api/v1/gdpr/data", headers=auth_headers)
        assert resp.status_code == 200


class TestScheduling:
    async def test_get_availability(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/scheduling/availability", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_set_availability(self, client: AsyncClient, auth_headers: dict):
        resp = await client.put(
            "/api/v1/scheduling/availability",
            json={
                "slots": [
                    {"day_of_week": 1, "start_time": "09:00", "end_time": "17:00"},
                    {"day_of_week": 3, "start_time": "10:00", "end_time": "18:00"},
                ]
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    async def test_schedule_interview(
        self, client: AsyncClient, auth_headers: dict, candidate_fixture: dict
    ):
        interview_resp = await client.post(
            "/api/v1/interviews",
            json={"candidate_id": candidate_fixture["id"], "question_count": 2},
            headers=auth_headers,
        )
        assert interview_resp.status_code == 201
        interview = interview_resp.json()

        resp = await client.post(
            "/api/v1/scheduling/schedule",
            json={
                "interview_id": interview["id"],
                "candidate_id": candidate_fixture["id"],
                "scheduled_at": "2026-07-01T14:00:00",
                "duration_minutes": 45,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "scheduled"

    async def test_list_scheduled(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/scheduling/scheduled", headers=auth_headers)
        assert resp.status_code == 200
        assert "items" in resp.json()

    async def test_cancel_scheduled_not_found(self, client: AsyncClient, auth_headers: dict):
        resp = await client.delete(
            "/api/v1/scheduling/scheduled/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestBulk:
    async def test_bulk_import_candidates(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/api/v1/bulk/import/candidates",
            json={
                "candidates": [
                    {"name": "Bulk One", "email": "bulk1@test.com"},
                    {"name": "Bulk Two", "email": "bulk2@test.com"},
                ]
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["created"] == 2

    async def test_bulk_status(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/api/v1/bulk/status",
            json={"entity_type": "candidates", "ids": ["00000000-0000-0000-0000-000000000000"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()[0]["exists"] is False


class TestProctoring:
    async def test_create_proctoring_session(
        self, client: AsyncClient, auth_headers: dict, interview_fixture: dict
    ):
        resp = await client.post(
            "/api/v1/proctoring/sessions",
            json={"interview_id": interview_fixture["id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"

    async def test_log_event(
        self, client: AsyncClient, auth_headers: dict, interview_fixture: dict
    ):
        session_resp = await client.post(
            "/api/v1/proctoring/sessions",
            json={"interview_id": interview_fixture["id"]},
            headers=auth_headers,
        )
        session_id = session_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/proctoring/sessions/{session_id}/events",
            json={"event_type": "looking_away", "severity": "medium", "confidence": 0.8},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["event_type"] == "looking_away"

    async def test_end_session(
        self, client: AsyncClient, auth_headers: dict, interview_fixture: dict
    ):
        session_resp = await client.post(
            "/api/v1/proctoring/sessions",
            json={"interview_id": interview_fixture["id"]},
            headers=auth_headers,
        )
        session_id = session_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/proctoring/sessions/{session_id}/end",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ended"

    async def test_list_sessions(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/proctoring/sessions", headers=auth_headers)
        assert resp.status_code == 200
        assert "items" in resp.json()


class TestPlagiarism:
    async def test_create_check(self, client: AsyncClient, auth_headers: dict):
        coding_resp = await client.post(
            "/api/v1/coding/questions",
            json={
                "title": "Test Question",
                "description": "Write a function",
                "language": "python",
                "code": "def test(): pass",
            },
            headers=auth_headers,
        )
        if coding_resp.status_code != 201:
            pytest.skip("Coding endpoint not available")

        question = coding_resp.json()

        sub_resp = await client.post(
            "/api/v1/coding/submissions",
            json={"question_id": question["id"], "code": "def test(): pass"},
            headers=auth_headers,
        )
        submission = sub_resp.json()

        resp = await client.post(
            "/api/v1/plagiarism/checks",
            json={"submission_id": submission["id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"

    async def test_list_checks(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/plagiarism/checks", headers=auth_headers)
        assert resp.status_code == 200
        assert "items" in resp.json()


class TestBranding:
    async def test_get_branding_no_org(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/branding", headers=auth_headers)
        assert resp.status_code in (200, 400)

    async def test_upsert_branding_no_org(self, client: AsyncClient, auth_headers: dict):
        resp = await client.put(
            "/api/v1/branding",
            json={"primary_color": "#ff0000"},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 400)
