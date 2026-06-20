"""Adaptive difficulty manager with rolling average."""

import logging
from typing import List

from app.core.constants import DifficultyLevel, DIFFICULTY_THRESHOLDS, ROLLING_WINDOW_SIZE

logger = logging.getLogger(__name__)


class DifficultyManager:
    def __init__(self, initial_level: int = DifficultyLevel.MEDIUM):
        self.current_level = initial_level
        self.score_history: List[float] = []
        self.level_history: List[int] = [initial_level]

    def add_score(self, score: float) -> int:
        self.score_history.append(score)
        new_level = self._calculate_level()
        if new_level != self.current_level:
            logger.info("Difficulty changed: %s -> %s", self.difficulty_name, DifficultyLevel.to_name(new_level))
            self.current_level = new_level
        self.level_history.append(self.current_level)
        return self.current_level

    def _calculate_level(self) -> int:
        if not self.score_history:
            return self.current_level
        avg = self._rolling_average
        if avg >= DIFFICULTY_THRESHOLDS["increase"]:
            return min(self.current_level + 1, DifficultyLevel.EXPERT)
        elif avg < DIFFICULTY_THRESHOLDS["decrease_low"]:
            return max(self.current_level - 1, DifficultyLevel.EASY)
        elif avg < DIFFICULTY_THRESHOLDS["maintain_low"]:
            if self.current_level > DifficultyLevel.MEDIUM:
                return self.current_level - 1
        return self.current_level

    @property
    def _rolling_average(self) -> float:
        window = self.score_history[-ROLLING_WINDOW_SIZE:]
        return sum(window) / len(window) if window else 0.0

    @property
    def difficulty_name(self) -> str:
        return DifficultyLevel.to_name(self.current_level)

    @property
    def average_score(self) -> float:
        return sum(self.score_history) / len(self.score_history) if self.score_history else 0.0

    def get_stats(self) -> dict:
        return {
            "current_level": self.current_level,
            "current_level_name": self.difficulty_name,
            "rolling_average": round(self._rolling_average, 1),
            "average_score": round(self.average_score, 1),
            "total_scores": len(self.score_history),
            "score_history": self.score_history.copy(),
            "level_history": self.level_history.copy(),
        }

    def reset(self, level: int = DifficultyLevel.MEDIUM) -> None:
        self.current_level = level
        self.score_history = []
        self.level_history = [level]
