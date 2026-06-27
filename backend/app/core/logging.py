"""Structured logging setup using structlog.

Console-friendly in development; JSON in production (``LOG_JSON=true``).
A ``request_id`` context variable is bound per-request by middleware so every
log line within a request is correlated.
"""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar

import structlog

# Per-request correlation id, set by RequestContextMiddleware.
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def _add_request_id(_: object, __: str, event_dict: dict[str, object]) -> dict[str, object]:
    rid = request_id_ctx.get()
    if rid is not None:
        event_dict["request_id"] = rid
    return event_dict


def configure_logging(*, level: str = "INFO", json_logs: bool = False) -> None:
    """Configure structlog + stdlib logging once at startup."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _add_request_id,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_logs:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Route stdlib logging (uvicorn, sqlalchemy) through the same level.
    logging.basicConfig(level=log_level, handlers=[logging.StreamHandler(sys.stdout)])
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "elastic_transport"):
        logging.getLogger(noisy).setLevel(max(log_level, logging.WARNING))


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger."""
    return structlog.get_logger(name)  # type: ignore[no-any-return]
