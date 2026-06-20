from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


async def http_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "detail": exc.detail,
            "request_id": getattr(request.state, "request_id", None),
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg", "Invalid value"),
            }
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"status": "error", "detail": "Validation failed", "errors": errors},
    )


async def generic_exception_handler(request: Request, exc: Exception):
    import logging
    logger = logging.getLogger(__name__)
    logger.error("Unhandled exception: %s: %s", type(exc).__name__, str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "detail": "Internal server error",
            "request_id": getattr(request.state, "request_id", None),
        },
    )
