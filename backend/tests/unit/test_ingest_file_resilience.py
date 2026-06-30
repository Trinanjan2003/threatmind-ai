"""Cover IngestFileUseCase degradation paths (search/alert failures)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from app.application.ingestion.ingest_file import IngestFileUseCase
from app.domain.entities.alert import Alert
from app.domain.enums import DataSourceType
from app.domain.events.normalized_event import NormalizedEvent

_SAMPLE = Path(__file__).resolve().parents[2] / "app" / "data" / "samples" / "sysmon_sample.jsonl"


class _FailingSearch:
    """Search store whose indexing always fails — ingestion must still proceed."""

    async def index_events(self, events: Sequence[NormalizedEvent]) -> int:
        raise RuntimeError("ES down")

    async def search_events(self, **_: object):  # pragma: no cover
        return [], 0

    async def get_event(self, event_id: str):  # pragma: no cover
        return None

    async def health(self) -> bool:
        return False


class _FailingAlertRepo:
    """Alert repo whose add() always fails — ingestion must not crash."""

    async def add(self, alert: Alert) -> Alert:
        raise RuntimeError("DB down")

    async def get_by_id(self, *_): ...  # pragma: no cover
    async def search(self, *_): ...  # pragma: no cover
    async def update(self, *_): ...  # pragma: no cover
    async def count_by_status(self): ...  # pragma: no cover
    async def count_by_severity(self): ...  # pragma: no cover


@pytest.mark.unit
async def test_ingest_survives_search_and_alert_failures() -> None:
    uc = IngestFileUseCase(search=_FailingSearch(), alerts=_FailingAlertRepo())  # type: ignore[arg-type]
    summary = await uc.execute(source_type=DataSourceType.SYSMON, content=_SAMPLE.read_bytes())

    # Parsing still worked; indexing failed gracefully (0), alert persistence
    # failed gracefully (0) — but the use case returned a coherent summary.
    assert summary.events_parsed >= 4
    assert summary.events_indexed == 0
    assert summary.alerts_created == 0
    assert summary.source_type == "sysmon"
