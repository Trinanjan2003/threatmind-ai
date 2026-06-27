"""Prometheus metrics and OpenTelemetry wiring."""

from __future__ import annotations

from fastapi import FastAPI
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

REQUEST_COUNT = Counter(
    "threatmind_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "threatmind_http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
)
AGENT_RUNS = Counter(
    "threatmind_agent_runs_total",
    "Total agent runs",
    ["agent", "status"],
)
LLM_LATENCY = Histogram(
    "threatmind_llm_request_duration_seconds",
    "LLM request latency",
    ["operation"],
)


def setup_observability(app: FastAPI) -> None:
    """Attach the /metrics endpoint and optional OpenTelemetry instrumentation."""
    if settings.prometheus_enabled:

        @app.get("/metrics", include_in_schema=False)
        async def metrics(_: Request) -> Response:
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    if settings.otel_enabled:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            FastAPIInstrumentor.instrument_app(app)
            logger.info("otel_instrumentation_enabled")
        except Exception as exc:  # noqa: BLE001 - optional dependency path
            logger.warning("otel_instrumentation_failed", error=str(exc))
