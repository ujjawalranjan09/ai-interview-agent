"""Greenhouse ATS integration using Harvest API."""
from typing import Any, Dict, List, Optional
import httpx

from app.models.candidate import Candidate
from app.models.interview import Interview
from app.services.ats.base import ATSIntegration


class GreenhouseIntegration(ATSIntegration):
    BASE_URL = "https://harvest.greenhouse.io/v1"

    async def _request(self, method: str, path: str, json: Optional[dict] = None) -> dict:
        auth = (self.config.get("api_key", ""), "")
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.request(method, f"{self.BASE_URL}{path}", auth=auth, json=json)
            resp.raise_for_status()
            return resp.json()

    async def push_candidate(self, candidate: Candidate) -> str:
        data = {
            "first_name": candidate.name.split(" ")[0] if candidate.name else "",
            "last_name": " ".join(candidate.name.split(" ")[1:]) if candidate.name and " " in candidate.name else "",
            "email": candidate.email or "",
        }
        result = await self._request("POST", "/candidates", json=data)
        return str(result.get("id", ""))

    async def push_interview(self, interview: Interview, external_candidate_id: str) -> str:
        scorecard = {
            "candidate_id": int(external_candidate_id),
            "score": interview.total_score,
            "notes": f"AI Interview completed. Score: {interview.total_score:.1f}. Questions: {interview.questions_answered}",
        }
        result = await self._request("POST", "/scorecards", json=scorecard)
        return str(result.get("id", ""))

    async def pull_candidates(self) -> List[Dict[str, Any]]:
        result = await self._request("GET", "/candidates?per_page=50")
        return result.get("items", result) if isinstance(result, dict) else result

    async def sync_status(self, external_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/candidates/{external_id}")
