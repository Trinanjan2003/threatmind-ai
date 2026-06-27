"""FastAPI application factory and entrypoint.

Composition root: builds the app, configures logging/observability, registers
middleware (request-context, security headers, CORS, rate limiting), mounts the
v1 router, and manages startup/shutdown of shared resources via lifespan.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.middleware import (
    RateLimitMiddleware,
    RequestContextMiddleware,
    SecurityHeadersMiddleware,
    register_exception_handlers,
)
from app.api.v1.router import api_router
from app.container import container
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.observability import setup_observability

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging(level=settings.log_level, json_logs=settings.log_json)
    settings.assert_production_safe()
    logger.info(
        "startup",
        project=settings.project_name,
        environment=settings.environment,
        version=__version__,
    )

    # Best-effort: ensure the events index exists (non-fatal if ES is down).
    try:
        from app.infrastructure.search.elasticsearch_search import ElasticsearchSearch

        if isinstance(container.search, ElasticsearchSearch):
            await container.search.ensure_indices()
    except Exception as exc:  # noqa: BLE001 - ES may not be ready at boot
        logger.warning("es_index_init_skipped", error=str(exc))

    try:
        yield
    finally:
        await container.aclose()
        from app.infrastructure.db.session import dispose_engine

        await dispose_engine()
        logger.info("shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.project_name,
        version=__version__,
        description="Enterprise AI threat-hunting platform — free & local.",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware (order matters: outermost first) ──
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, cache=container.cache)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Remaining"],
    )
    app.add_middleware(RequestContextMiddleware)

    # ── Errors, metrics, routes ──
    register_exception_handlers(app)
    setup_observability(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "name": settings.project_name,
            "version": __version__,
            "docs": "/docs",
        }

    return app


app = create_app()
