"""End-to-end: ingest sample Sysmon telemetry → detection → alerts.

Exercises the ingestion use case with in-memory fakes for the search and alert
ports, so it runs without external infrastructure while validating the full
parse → index → detect → persist flow.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from app.application.ingestion.ingest_file import IngestFileUseCase
from app.domain.entities.alert import Alert
from app.domain.enums import DataSourceType
from app.domain.events.normalized_event import NormalizedEvent

_SAMPLE = Path(__file__).resolve().parents[2] / "app" / "data" / "samples" / "sysmon_sample.jsonl"


class _FakeSearch:
    def __init__(self) -> None:
        self.indexed: list[NormalizedEvent] = []

    async def index_events(self, events: Sequence[NormalizedEvent]) -> int:
        self.indexed.extend(events)
        return len(events)

    async def search_events(self, **_: object):  # pragma: no cover
        return [], 0

    async def get_event(self, event_id: str):  # pragma: no cover
        return None

    async def health(self) -> bool:
        return True


class _FakeAlertRepo:
    def __init__(self) -> None:
        self.added: list[Alert] = []

    async def add(self, alert: Alert) -> Alert:
        self.added.append(alert)
        return alert

    # Unused abstract methods for this flow.
    async def get_by_id(self, *_): ...  # pragma: no cover
    async def search(self, *_): ...  # pragma: no cover
    async def update(self, *_): ...  # pragma: no cover
    async def count_by_status(self): ...  # pragma: no cover
    async def count_by_severity(self): ...  # pragma: no cover


@pytest.mark.e2e
async def test_sysmon_ingest_produces_alerts() -> None:
    search = _FakeSearch()
    alerts = _FakeAlertRepo()
    uc = IngestFileUseCase(search=search, alerts=alerts)  # type: ignore[arg-type]

    content = _SAMPLE.read_bytes()
    summary = await uc.execute(source_type=DataSourceType.SYSMON, content=content)

    assert summary.events_parsed >= 4
    assert summary.events_indexed == summary.events_parsed
    # The sample contains encoded PowerShell from Word + a temp-service + ransomware ext.
    assert summary.alerts_created >= 3
    assert all(a.evidence for a in alerts.added)
    titles = {a.title for a in alerts.added}
    assert any("PowerShell" in t for t in titles)
