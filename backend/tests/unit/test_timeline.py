"""Unit tests for attack-timeline reconstruction."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.application.reporting.timeline import reconstruct_timeline
from app.domain.entities.alert import Alert
from app.domain.enums import AlertCategory, AlertSource, Severity
from app.domain.value_objects.confidence import ConfidenceScore
from app.domain.value_objects.evidence import Evidence
from app.infrastructure.mitre.knowledge_base import technique_value_object


def _alert(title: str, technique_id: str, when: datetime) -> Alert:
    return Alert(
        id=uuid.uuid4(),
        title=title,
        description=title,
        category=AlertCategory.OTHER,
        severity=Severity.HIGH,
        confidence=ConfidenceScore(70),
        source=AlertSource.RULE,
        techniques=[technique_value_object(technique_id)],  # type: ignore[list-item]
        evidence=[Evidence(summary="e", event_id="ev")],
        first_seen=when,
    )


def test_timeline_orders_by_kill_chain() -> None:
    # Provide alerts out of kill-chain order; expect them reordered.
    base = datetime(2026, 6, 27, 9, 0, tzinfo=UTC)
    alerts = [
        _alert("Ransomware impact", "T1486", base),
        _alert("Phishing attachment", "T1566.001", base),
        _alert("LSASS dump", "T1003.001", base),
    ]
    steps = reconstruct_timeline(alerts)
    phases = [s.phase for s in steps]
    # initial_access should come before credential_access before impact.
    assert phases.index("initial_access") < phases.index("credential_access")
    assert phases.index("credential_access") < phases.index("impact")
    assert [s.order_index for s in steps] == [0, 1, 2]


def test_empty_alerts_yield_empty_timeline() -> None:
    assert reconstruct_timeline([]) == []
