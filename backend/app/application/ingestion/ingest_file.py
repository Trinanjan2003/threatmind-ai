"""IngestFileUseCase — orchestrates ingestion of an uploaded log file.

Flow: select parser → parse to normalized events → index events into the search
store → run detection rules → persist generated alerts. Search/alert failures
degrade gracefully so a partial outage doesn't lose the whole ingest.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.detection.engine import DetectionEngine
from app.application.ports.search import SearchPort
from app.core.logging import get_logger
from app.domain.enums import DataSourceType
from app.domain.repositories.alert_repository import AlertRepository
from app.infrastructure.parsers.registry import get_parser

logger = get_logger(__name__)


@dataclass(slots=True)
class IngestSummary:
    source_type: str
    events_parsed: int
    events_indexed: int
    parse_errors: int
    alerts_created: int


class IngestFileUseCase:
    def __init__(
        self,
        *,
        search: SearchPort,
        alerts: AlertRepository,
        engine: DetectionEngine | None = None,
    ) -> None:
        self._search = search
        self._alerts = alerts
        self._engine = engine or DetectionEngine()

    async def execute(
        self, *, source_type: DataSourceType, content: bytes, job_id: str | None = None
    ) -> IngestSummary:
        parser = get_parser(source_type)
        result = parser.parse(content)

        for event in result.events:
            event.ingest_job_id = job_id

        # Index events (best-effort — detection still runs if indexing fails).
        indexed = 0
        try:
            indexed = await self._search.index_events(result.events)
        except Exception as exc:  # noqa: BLE001
            logger.warning("event_indexing_failed", error=str(exc))

        # Run detection and persist alerts.
        alerts = self._engine.evaluate(result.events)
        created = 0
        for alert in alerts:
            try:
                await self._alerts.add(alert)
                created += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning("alert_persist_failed", error=str(exc), alert=alert.title)

        logger.info(
            "ingest_complete",
            source_type=source_type.value,
            parsed=len(result.events),
            indexed=indexed,
            errors=len(result.errors),
            alerts=created,
        )
        return IngestSummary(
            source_type=source_type.value,
            events_parsed=len(result.events),
            events_indexed=indexed,
            parse_errors=len(result.errors),
            alerts_created=created,
        )
