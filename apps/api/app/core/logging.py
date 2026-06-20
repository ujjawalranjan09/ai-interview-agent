"""Structured logging configuration."""
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict

import structlog


def add_app_context(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    event_dict["service"] = "ai-interview-agent"
    event_dict["environment"] = "production"
    return event_dict


def add_timestamp(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    event_dict["timestamp"] = datetime.now(timezone.utc).isoformat()
    return event_dict


def setup_logging() -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            add_timestamp,
            add_app_context,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer() if sys.stderr.isatty() else structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
