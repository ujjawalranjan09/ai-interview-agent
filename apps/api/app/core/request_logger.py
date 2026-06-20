import time
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = int((time.monotonic() - start) * 1000)

        extra = {
            "request_id": getattr(request.state, "request_id", None),
            "duration_ms": duration_ms,
            "method": request.method,
            "path": request.url.path,
        }
        logger.info(f"{request.method} {request.url.path} {response.status_code}", extra=extra)
        return response
