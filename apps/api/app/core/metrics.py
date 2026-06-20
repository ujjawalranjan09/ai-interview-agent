"""Prometheus metrics setup."""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from time import time
import re

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0),
)

active_users = Gauge("active_users", "Currently active users")
active_interviews = Gauge("active_interviews", "Currently active interviews")

safe_endpoint_pattern = re.compile(r"[^a-zA-Z0-9_\-/]")


def _safe_endpoint(path: str) -> str:
    cleaned = safe_endpoint_pattern.sub("_", path)
    return cleaned or "unknown"


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method
        path = _safe_endpoint(request.url.path)
        start = time()
        try:
            response = await call_next(request)
            status = str(response.status_code)
            return response
        except Exception:
            status = "500"
            raise
        finally:
            elapsed = time() - start
            http_requests_total.labels(method=method, endpoint=path, status=status).inc()
            http_request_duration_seconds.labels(method=method, endpoint=path).observe(elapsed)


async def metrics_endpoint(request: Request) -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
