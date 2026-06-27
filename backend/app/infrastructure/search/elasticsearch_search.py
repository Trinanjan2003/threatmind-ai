"""Elasticsearch implementation of SearchPort.

Builds structured queries (never raw user-concatenated DSL) over the
normalized-events index. Degrades gracefully via ``health()``.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

from app.application.ports.search import SearchPort
from app.core.config import settings
from app.core.logging import get_logger
from app.domain.events.normalized_event import NormalizedEvent

logger = get_logger(__name__)


class ElasticsearchSearch(SearchPort):
    def __init__(self, client: AsyncElasticsearch | None = None) -> None:
        self._client = client or AsyncElasticsearch(settings.elasticsearch_url)
        self._events_index = f"{settings.elasticsearch_index_prefix}-events"

    async def index_events(self, events: Sequence[NormalizedEvent]) -> int:
        if not events:
            return 0
        actions = [
            {
                "_index": self._events_index,
                "_id": event.fingerprint(),  # idempotent: dedup by content hash
                "_source": event.to_document(),
            }
            for event in events
        ]
        success, _ = await async_bulk(self._client, actions, raise_on_error=False)
        return int(success)

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
    ) -> tuple[list[dict[str, Any]], int]:
        must: list[dict[str, Any]] = []
        if query:
            must.append({"multi_match": {"query": query, "fields": ["message", "action", "raw.*"]}})
        filters: list[dict[str, Any]] = []
        if host:
            filters.append({"term": {"host": host}})
        if user:
            filters.append({"term": {"user": user}})
        if source_type:
            filters.append({"term": {"source_type": source_type}})
        if time_from or time_to:
            rng: dict[str, str] = {}
            if time_from:
                rng["gte"] = time_from.isoformat()
            if time_to:
                rng["lte"] = time_to.isoformat()
            filters.append({"range": {"@timestamp": rng}})

        body = {
            "query": {"bool": {"must": must or [{"match_all": {}}], "filter": filters}},
            "sort": [{"@timestamp": {"order": "desc"}}],
            "from": offset,
            "size": limit,
        }
        resp = await self._client.search(index=self._events_index, body=body)
        hits = resp["hits"]
        items = [{"id": h["_id"], **h["_source"]} for h in hits["hits"]]
        total = hits["total"]["value"] if isinstance(hits["total"], dict) else hits["total"]
        return items, int(total)

    async def get_event(self, event_id: str) -> dict[str, Any] | None:
        if not await self._client.exists(index=self._events_index, id=event_id):
            return None
        doc = await self._client.get(index=self._events_index, id=event_id)
        return {"id": doc["_id"], **doc["_source"]}

    async def ensure_indices(self) -> None:
        """Create the events index with a basic mapping if it does not exist."""
        if await self._client.indices.exists(index=self._events_index):
            return
        await self._client.indices.create(
            index=self._events_index,
            body={
                "mappings": {
                    "properties": {
                        "@timestamp": {"type": "date"},
                        "source_type": {"type": "keyword"},
                        "action": {"type": "keyword"},
                        "host": {"type": "keyword"},
                        "user": {"type": "keyword"},
                        "severity": {"type": "keyword"},
                        "message": {"type": "text"},
                        "event_hash": {"type": "keyword"},
                    }
                }
            },
        )

    async def health(self) -> bool:
        try:
            return bool(await self._client.ping())
        except Exception as exc:  # noqa: BLE001 - health must never raise
            logger.warning("elasticsearch_health_check_failed", error=str(exc))
            return False

    async def close(self) -> None:
        await self._client.close()
