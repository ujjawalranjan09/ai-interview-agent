"""State machine for interview flow control."""

import logging
from typing import Any, Callable, Dict, List

from app.core.constants import InterviewState, STATE_TRANSITIONS

logger = logging.getLogger(__name__)


class StateMachine:
    def __init__(self):
        self._current_state = InterviewState.IDLE
        self._history: List[str] = []
        self._listeners: Dict[str, List[Callable]] = {}
        self._transition_count = 0

    @property
    def current_state(self) -> str:
        return self._current_state

    @property
    def history(self) -> List[str]:
        return self._history.copy()

    def can_transition(self, target_state: str) -> bool:
        return target_state in STATE_TRANSITIONS.get(self._current_state, [])

    def transition(self, target_state: str) -> bool:
        if not self.can_transition(target_state):
            logger.warning("Invalid transition: %s -> %s", self._current_state, target_state)
            return False
        old = self._current_state
        self._history.append(old)
        self._current_state = target_state
        self._transition_count += 1
        self._notify_listeners(old, target_state)
        return True

    def force_transition(self, target_state: str) -> None:
        old = self._current_state
        self._history.append(old)
        self._current_state = target_state
        self._transition_count += 1
        self._notify_listeners(old, target_state)

    def reset(self) -> None:
        self._current_state = InterviewState.IDLE
        self._history = []
        self._transition_count = 0

    def on_transition(self, from_state: str, callback: Callable) -> None:
        key = from_state if from_state != "*" else "__all__"
        self._listeners.setdefault(key, []).append(callback)

    def _notify_listeners(self, old_state: str, new_state: str) -> None:
        for cb in self._listeners.get(old_state, []) + self._listeners.get("__all__", []):
            try:
                cb(old_state, new_state)
            except Exception as e:
                logger.error("Listener error: %s", e)

    @property
    def is_terminal(self) -> bool:
        return self._current_state in (InterviewState.COMPLETED, InterviewState.ERROR)

    @property
    def is_active(self) -> bool:
        return self._current_state not in (InterviewState.IDLE, InterviewState.COMPLETED, InterviewState.ERROR)

    def get_next_states(self) -> List[str]:
        return STATE_TRANSITIONS.get(self._current_state, [])

    def get_stats(self) -> Dict[str, Any]:
        return {
            "current_state": self._current_state,
            "transition_count": self._transition_count,
            "history_length": len(self._history),
            "is_active": self.is_active,
            "is_terminal": self.is_terminal,
            "next_states": self.get_next_states(),
        }
