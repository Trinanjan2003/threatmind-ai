"""Redis implementation of CachePort (cache, atomic counters, pub/sub)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import redis.asyncio as aioredis

from app.application.ports.cache import CachePort
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RedisCache(CachePort):
    # redis-py's async type stubs are incomplete (decode_responses, aclose);
    # we keep the client loosely typed and rely on runtime behavior + tests.
    def __init__(self, client: Any = None) -> None:
        self._client: Any = client or aioredis.from_url(
            settings.redis_dsn, encoding="utf-8", decode_responses=True
        )

    async def get(self, key: str) -> str | None:
        result = await self._client.get(key)
        return result if result is None else str(result)

    async def set(self, key: str, value: str, *, ttl_seconds: int | None = None) -> None:
        await self._client.set(key, value, ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def incr(self, key: str, *, ttl_seconds: int | None = None) -> int:
        async with self._client.pipeline(transaction=True) as pipe:
            pipe.incr(key)
            if ttl_seconds is not None:
                # Only set expiry when the key is first created.
                pipe.expire(key, ttl_seconds, nx=True)
            results = await pipe.execute()
        return int(results[0])

    async def publish(self, channel: str, message: str) -> None:
        await self._client.publish(channel, message)

    async def subscribe(self, channel: str) -> AsyncIterator[str]:
        pubsub = self._client.pubsub()
        await pubsub.subscribe(channel)
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    yield str(message["data"])
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()

    async def health(self) -> bool:
        try:
            return bool(await self._client.ping())
        except Exception as exc:  # noqa: BLE001 - health must never raise
            logger.warning("redis_health_check_failed", error=str(exc))
            return False

    async def close(self) -> None:
        await self._client.aclose()
