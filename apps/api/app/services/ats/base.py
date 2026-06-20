"""Abstract base class for ATS integrations."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from app.models.candidate import Candidate
from app.models.interview import Interview


class ATSIntegration(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    async def push_candidate(self, candidate: Candidate) -> str:
        pass

    @abstractmethod
    async def push_interview(self, interview: Interview, external_candidate_id: str) -> str:
        pass

    @abstractmethod
    async def pull_candidates(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def sync_status(self, external_id: str) -> Dict[str, Any]:
        pass
