"""Search port for normalized events (implemented by Elasticsearch)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from app.domain.events.normalized_event import NormalizedEvent


class SearchPort(ABC):
    @abstractmethod
    async def index_events(self, events: Sequence[NormalizedEvent]) -> int:
        """Bulk-index events; returns the number successfully indexed."""

    @abstractmethod
    async def search_events(
        self,
        *,
        query: str | None = None,
        host: str | None = None,
        user: str | None = None,
        source_type: str | None = None,
        time_from: datetime | None = None,
        time_to: datetime | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[dict[str, Any]], int]: ...

    @abstractmethod
    async def get_event(self, event_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    async def health(self) -> bool: ...
