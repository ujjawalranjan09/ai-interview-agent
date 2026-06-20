"""FastAPI application factory."""

from contextlib import asynccontextmanager
from datetime import datetime
from os import environ

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.database import engine
from app.core.logging_config import setup_logging
from app.core.logging import setup_logging as setup_structured_logging
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.request_id import RequestIDMiddleware
from app.core.request_logger import RequestLoggingMiddleware
from app.core.cache import CacheControlMiddleware
from app.core.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)
from app.core.metrics import MetricsMiddleware, metrics_endpoint
from app.api.v1.router import api_router
from app.api.v1.ws import router as ws_router

if environ.get("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=environ["SENTRY_DSN"],
        environment=environ.get("ENVIRONMENT", "production"),
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
    )

_start_time = datetime.utcnow()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.LOG_LEVEL)
    setup_structured_logging()
    yield
    await engine.dispose()


app = FastAPI(
    title="AI Interview Agent API",
    description="Backend API for AI-powered interview platform",
    version="1.0.0",
    contact={"email": "support@interviewagent.com"},
    license_info={"name": "MIT"},
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CacheControlMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(MetricsMiddleware)

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.include_router(api_router)
app.include_router(ws_router)

app.add_route("/metrics", metrics_endpoint, include_in_schema=False)


@app.get("/health")
async def root_health_check():
    checks = {"database": "unknown", "service": "ok"}
    try:
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"
    return {
        "status": "healthy" if checks["database"] == "ok" else "degraded",
        "version": "1.0.0",
        "uptime": (datetime.utcnow() - _start_time).seconds,
        "checks": checks,
    }
