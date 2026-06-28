"""Unit tests for the normalized event schema."""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.enums import DataSourceType
from app.domain.events.normalized_event import NetworkInfo, NormalizedEvent, ProcessInfo


def _event(**kw: object) -> NormalizedEvent:
    defaults = {
        "timestamp": datetime(2026, 6, 27, 9, 0, tzinfo=UTC),
        "source_type": DataSourceType.SYSMON,
        "action": "process_create",
    }
    defaults.update(kw)
    return NormalizedEvent(**defaults)  # type: ignore[arg-type]


def test_fingerprint_is_stable_and_unique() -> None:
    e1 = _event(host="WIN-001", raw={"a": 1})
    e2 = _event(host="WIN-001", raw={"a": 1})
    e3 = _event(host="WIN-002", raw={"a": 1})
    assert e1.fingerprint() == e2.fingerprint()  # deterministic
    assert e1.fingerprint() != e3.fingerprint()  # host differs


def test_to_document_has_timestamp_and_hash() -> None:
    e = _event(
        host="WIN-001",
        process=ProcessInfo(name="powershell.exe", command_line="-enc"),
        network=NetworkInfo(dst_ip="10.0.0.1"),
    )
    doc = e.to_document()
    assert doc["@timestamp"].startswith("2026-06-27")
    assert doc["source_type"] == "sysmon"
    assert "event_hash" in doc
    assert "timestamp" not in doc  # replaced by @timestamp
