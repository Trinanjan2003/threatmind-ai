"""Unit tests for the detection engine and rules."""

from __future__ import annotations

import json

from app.application.detection.engine import DetectionEngine
from app.domain.enums import AlertCategory, Severity
from app.infrastructure.parsers import CloudTrailParser, SysmonParser


def _sysmon_event(record: dict) -> object:
    return SysmonParser().parse(json.dumps(record)).events[0]


class TestDetectionEngine:
    def test_encoded_powershell_detected(self) -> None:
        ev = _sysmon_event(
            {
                "EventID": 1,
                "Image": "powershell.exe",
                "CommandLine": "powershell.exe -EncodedCommand SQBFAFgA",
                "Computer": "WIN-001",
            }
        )
        alerts = DetectionEngine().evaluate_event(ev)
        assert any(a.category == AlertCategory.LOTL for a in alerts)
        assert all(a.evidence for a in alerts)  # every alert cites evidence

    def test_office_spawning_powershell_is_high_severity(self) -> None:
        ev = _sysmon_event(
            {
                "EventID": 1,
                "Image": "powershell.exe",
                "ParentImage": "winword.exe",
                "CommandLine": "powershell.exe whoami",
                "Computer": "WIN-002",
            }
        )
        alerts = DetectionEngine().evaluate_event(ev)
        titles = {a.title for a in alerts}
        assert "Office application spawned a script interpreter" in titles
        office_alert = next(a for a in alerts if "Office" in a.title)
        assert office_alert.severity == Severity.HIGH
        assert office_alert.techniques  # MITRE mapping attached

    def test_iam_priv_esc_detected_from_cloudtrail(self) -> None:
        payload = {
            "Records": [
                {
                    "eventTime": "2026-06-27T09:30:00Z",
                    "eventSource": "iam.amazonaws.com",
                    "eventName": "AttachUserPolicy",
                    "userIdentity": {"userName": "intern"},
                    "readOnly": False,
                }
            ]
        }
        events = CloudTrailParser().parse(json.dumps(payload)).events
        alerts = DetectionEngine().evaluate(events)
        assert any(a.category == AlertCategory.CLOUD_ATTACK for a in alerts)
        assert any(a.severity == Severity.CRITICAL for a in alerts)

    def test_benign_event_produces_no_alerts(self) -> None:
        ev = _sysmon_event(
            {"EventID": 1, "Image": "notepad.exe", "CommandLine": "notepad.exe", "Computer": "WIN-003"}
        )
        assert DetectionEngine().evaluate_event(ev) == []

    def test_rule_count_nonzero(self) -> None:
        assert DetectionEngine().rule_count >= 8
