"""Health and readiness probes."""

from __future__ import annotations

from fastapi import APIRouter

from app.container import container

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", summary="Liveness probe")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", summary="Readiness probe")
async def ready() -> dict[str, object]:
    """Report dependency health. AI (Ollama) being down is non-fatal."""
    cache_ok = await container.cache.health()
    search_ok = await container.search.health()
    llm_ok = await container.llm.health()

    # Cache + search are required; LLM is optional (graceful degradation).
    ready = cache_ok and search_ok
    return {
        "status": "ready" if ready else "degraded",
        "checks": {
            "redis": cache_ok,
            "elasticsearch": search_ok,
            "ollama": llm_ok,
        },
        "ai_features": "available" if llm_ok else "degraded",
    }
