"""Cache + pub/sub port (implemented by Redis)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class CachePort(ABC):
    @abstractmethod
    async def get(self, key: str) -> str | None: ...

    @abstractmethod
    async def set(self, key: str, value: str, *, ttl_seconds: int | None = None) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def incr(self, key: str, *, ttl_seconds: int | None = None) -> int:
        """Atomically increment a counter, optionally setting TTL on first write."""

    @abstractmethod
    async def publish(self, channel: str, message: str) -> None: ...

    @abstractmethod
    def subscribe(self, channel: str) -> AsyncIterator[str]: ...

    @abstractmethod
    async def health(self) -> bool: ...
