import os
import time
from collections import defaultdict


_limits: dict[str, list[float]] = defaultdict(list)
_DISABLED: bool = os.environ.get("DISABLE_RATE_LIMIT", "").lower() in ("1", "true", "yes")


def disable_rate_limit() -> None:
    global _DISABLED
    _DISABLED = True


def enable_rate_limit() -> None:
    global _DISABLED
    _DISABLED = False


def rate_limit(key: str, limit: int, window: int = 60) -> bool:
    if _DISABLED:
        return True
    now = time.time()
    window_start = now - window
    if key in _limits:
        _limits[key] = [t for t in _limits[key] if t > window_start]
    else:
        _limits[key] = []
    if len(_limits[key]) >= limit:
        return False
    _limits[key].append(now)
    return True
