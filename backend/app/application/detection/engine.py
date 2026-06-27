"""Detection engine — evaluates rules over normalized events to produce alerts.

Pure application logic: takes events + rules, returns Alert entities. Persistence
and indexing are handled by the ingestion use case. This separation keeps the
engine fully unit-testable without any I/O.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Sequence

from app.application.detection.rules import DEFAULT_RULES, DetectionRule
from app.domain.entities.alert import Alert
from app.domain.enums import AlertSource
from app.domain.events.normalized_event import NormalizedEvent
from app.domain.value_objects.confidence import ConfidenceScore
from app.domain.value_objects.evidence import Evidence
from app.infrastructure.mitre.knowledge_base import technique_value_object


class DetectionEngine:
    def __init__(self, rules: Sequence[DetectionRule] | None = None) -> None:
        self._rules = list(rules) if rules is not None else list(DEFAULT_RULES)

    @property
    def rule_count(self) -> int:
        return len(self._rules)

    def evaluate_event(self, event: NormalizedEvent) -> list[Alert]:
        """Return alerts produced by all rules matching a single event."""
        alerts: list[Alert] = []
        for rule in self._rules:
            if rule.matches(event):
                alerts.append(self._build_alert(rule, event))
        return alerts

    def evaluate(self, events: Iterable[NormalizedEvent]) -> list[Alert]:
        """Evaluate a batch of events; returns all generated alerts."""
        alerts: list[Alert] = []
        for event in events:
            alerts.extend(self.evaluate_event(event))
        return alerts

    def _build_alert(self, rule: DetectionRule, event: NormalizedEvent) -> Alert:
        techniques = [
            t for tid in rule.technique_ids if (t := technique_value_object(tid)) is not None
        ]
        evidence = [
            Evidence(
                summary=event.message or rule.description,
                event_id=event.fingerprint(),
                source=event.source_type.value,
                fields={
                    "action": event.action,
                    "process": event.process.command_line if event.process else None,
                },
            )
        ]
        return Alert(
            id=uuid.uuid4(),
            title=rule.title,
            description=rule.description,
            category=rule.category,
            severity=rule.severity,
            confidence=ConfidenceScore(rule.base_confidence),
            source=AlertSource.RULE,
            host=event.host,
            user_principal=event.user,
            explanation=rule.explanation or rule.description,
            evidence=evidence,
            techniques=techniques,
            first_seen=event.timestamp,
            last_seen=event.timestamp,
        )
