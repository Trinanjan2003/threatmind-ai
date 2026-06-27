"""Unit tests for the Alert domain entity behavior."""

from __future__ import annotations

import uuid

import pytest

from app.domain.entities.alert import Alert
from app.domain.enums import AlertCategory, AlertSource, AlertStatus, Severity
from app.domain.exceptions import InvariantViolationError
from app.domain.value_objects.confidence import ConfidenceScore
from app.domain.value_objects.evidence import Evidence


def _alert(**overrides: object) -> Alert:
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "title": "Suspicious PowerShell",
        "description": "Encoded command execution",
        "category": AlertCategory.LOTL,
        "severity": Severity.HIGH,
        "confidence": ConfidenceScore(80),
        "source": AlertSource.AI,
    }
    defaults.update(overrides)
    return Alert(**defaults)  # type: ignore[arg-type]


def test_new_alert_is_open() -> None:
    alert = _alert()
    assert not alert.is_closed
    assert alert.is_ai_generated


def test_assign_moves_new_to_triaging() -> None:
    alert = _alert(status=AlertStatus.NEW)
    user_id = uuid.uuid4()
    alert.assign(user_id)
    assert alert.assigned_to == user_id
    assert alert.status == AlertStatus.TRIAGING


def test_cannot_assign_closed_alert() -> None:
    alert = _alert(status=AlertStatus.RESOLVED)
    with pytest.raises(InvariantViolationError):
        alert.assign(uuid.uuid4())


def test_close_requires_closing_status() -> None:
    alert = _alert()
    with pytest.raises(InvariantViolationError):
        alert.close(status=AlertStatus.INVESTIGATING)
    alert.close(status=AlertStatus.FALSE_POSITIVE)
    assert alert.is_closed


def test_ai_alert_requires_evidence() -> None:
    alert = _alert(source=AlertSource.AI, evidence=[])
    with pytest.raises(InvariantViolationError):
        alert.validate_ai_evidence()
    alert.evidence = [Evidence(summary="encoded cmd", event_id="abc")]
    alert.validate_ai_evidence()  # no raise


def test_rule_alert_does_not_require_evidence() -> None:
    alert = _alert(source=AlertSource.RULE, evidence=[])
    alert.validate_ai_evidence()  # no raise
