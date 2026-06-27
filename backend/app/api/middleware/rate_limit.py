"""Redis-backed sliding-window rate limiting middleware.

Keyed per client (authenticated user id when available, else client IP). Fails
open if Redis is unavailable so a cache outage doesn't take down the API.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.application.ports.cache import CachePort
from app.core.config import settings
from app.core.errors import error_envelope
from app.core.logging import get_logger

logger = get_logger(__name__)
Handler = Callable[[Request], Awaitable[Response]]

# Paths that should never be rate limited (health/metrics).
_EXEMPT_PREFIXES = ("/health", "/metrics", "/docs", "/redoc", "/openapi.json")


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: object, *, cache: CachePort) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._cache = cache
        self._limit = settings.rate_limit_requests
        self._window = settings.rate_limit_window_seconds

    def _client_key(self, request: Request) -> str:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            # Cheap, stable bucket without full token decode.
            return f"rl:tok:{hash(auth) & 0xFFFFFFFF}"
        client = request.client
        return f"rl:ip:{client.host}" if client else "rl:ip:unknown"

    async def dispatch(self, request: Request, call_next: Handler) -> Response:
        if any(request.url.path.startswith(p) for p in _EXEMPT_PREFIXES):
            return await call_next(request)

        key = self._client_key(request)
        try:
            count = await self._cache.incr(key, ttl_seconds=self._window)
        except Exception as exc:  # noqa: BLE001 - fail open on cache errors
            logger.warning("rate_limit_unavailable", error=str(exc))
            return await call_next(request)

        remaining = max(0, self._limit - count)
        if count > self._limit:
            return JSONResponse(
                status_code=429,
                headers={
                    "Retry-After": str(self._window),
                    "X-RateLimit-Limit": str(self._limit),
                    "X-RateLimit-Remaining": "0",
                },
                content=error_envelope(
                    code="RATE_LIMITED",
                    message="Too many requests",
                    details={"limit": self._limit, "window_seconds": self._window},
                    request_id=getattr(request.state, "request_id", None),
                ),
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self._limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
