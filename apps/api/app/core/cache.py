"""Cache control middleware and Redis caching layer."""
import json
import re
from typing import Any, Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings


class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            response.headers["Cache-Control"] = "no-store"
            return response

        path = request.url.path

        if re.match(r"/api/v1/analytics/", path):
            response.headers["Cache-Control"] = "public, max-age=60"
        elif re.match(r"/api/v1/candidates$", path):
            response.headers["Cache-Control"] = "public, max-age=30"
        elif re.match(r"/api/v1/interviews$", path):
            response.headers["Cache-Control"] = "public, max-age=10"
        elif re.match(r"/api/v1/admin/system/", path):
            response.headers["Cache-Control"] = "public, max-age=30"
        elif re.match(r"/api/v1/branding", path):
            response.headers["Cache-Control"] = "public, max-age=600"
        else:
            response.headers["Cache-Control"] = "public, max-age=5"

        response.headers["Vary"] = "Accept-Encoding"
        return response


try:
    import redis.asyncio as redis
    _redis: Optional[redis.Redis] = None

    async def get_redis() -> redis.Redis:
        global _redis
        if _redis is None:
            _redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        return _redis
except ImportError:
    _redis = None

    async def get_redis() -> None:
        return None


async def cache_get(key: str) -> Optional[Any]:
    try:
        r = await get_redis()
        if not r:
            return None
        data = await r.get(key)
        if data:
            return json.loads(data)
    except Exception:
        pass
    return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    try:
        r = await get_redis()
        if not r:
            return
        await r.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        pass


async def cache_delete(key: str) -> None:
    r = await get_redis()
    if not r:
        return
    await r.delete(key)


async def cache_delete_pattern(pattern: str) -> None:
    r = await get_redis()
    if not r:
        return
    async for key in r.scan_iter(pattern):
        await r.delete(key)


async def get_cached_or_compute(key: str, ttl: int, factory):
    cached = await cache_get(key)
    if cached is not None:
        return cached
    value = await factory()
    await cache_set(key, value, ttl)
    return value
