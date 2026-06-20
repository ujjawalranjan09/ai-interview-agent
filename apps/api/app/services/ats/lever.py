"""Lever ATS integration using Lever API."""
from typing import Any, Dict, List, Optional
import httpx
import base64

from app.models.candidate import Candidate
from app.models.interview import Interview
from app.services.ats.base import ATSIntegration


class LeverIntegration(ATSIntegration):
    BASE_URL = "https://api.lever.co/v1"

    async def _request(self, method: str, path: str, json: Optional[dict] = None) -> dict:
        api_key = self.config.get("api_key", "")
        token = base64.b64encode(f"{api_key}:".encode()).decode()
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.request(method, f"{self.BASE_URL}{path}",
                headers={"Authorization": f"Basic {token}"}, json=json)
            resp.raise_for_status()
            return resp.json()

    async def push_candidate(self, candidate: Candidate) -> str:
        data = {"name": candidate.name, "email": candidate.email, "source": "AI Interview Agent"}
        result = await self._request("POST", "/candidates", json=data)
        return result.get("data", {}).get("id", "")

    async def push_interview(self, interview: Interview, external_candidate_id: str) -> str:
        return "lever_interview_id_placeholder"

    async def pull_candidates(self) -> List[Dict[str, Any]]:
        result = await self._request("GET", "/candidates?limit=50")
        return result.get("data", [])

    async def sync_status(self, external_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/candidates/{external_id}")
