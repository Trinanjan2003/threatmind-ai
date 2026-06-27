"""Dependency-injection container.

Wires application ports to their concrete infrastructure adapters. Singletons
(LLM, cache, search) are created once and shared; per-request resources
(DB session and the repositories/use-cases built on it) are created by the
``request_scope`` factory in ``app.api.deps``.

This is the single composition root — the only place where the application
layer learns about concrete implementations (per the Clean Architecture
dependency rule).
"""

from __future__ import annotations

from app.application.ports.cache import CachePort
from app.application.ports.llm import LLMPort
from app.application.ports.search import SearchPort
from app.core.config import settings
from app.infrastructure.cache.redis_cache import RedisCache
from app.infrastructure.llm.ollama_provider import OllamaProvider
from app.infrastructure.search.elasticsearch_search import ElasticsearchSearch


class Container:
    """Holds long-lived singleton adapters."""

    def __init__(self) -> None:
        self._cache: CachePort | None = None
        self._search: SearchPort | None = None
        self._llm: LLMPort | None = None

    @property
    def cache(self) -> CachePort:
        if self._cache is None:
            self._cache = RedisCache()
        return self._cache

    @property
    def search(self) -> SearchPort:
        if self._search is None:
            self._search = ElasticsearchSearch()
        return self._search

    @property
    def llm(self) -> LLMPort:
        if self._llm is None:
            # Provider is pluggable via settings; only free/local providers allowed.
            if settings.llm_provider == "ollama":
                self._llm = OllamaProvider()
            else:  # pragma: no cover - guarded by settings Literal
                raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
        return self._llm

    async def aclose(self) -> None:
        if isinstance(self._cache, RedisCache):
            await self._cache.close()
        if isinstance(self._search, ElasticsearchSearch):
            await self._search.close()


# Module-level singleton, initialized in the app lifespan.
container = Container()
