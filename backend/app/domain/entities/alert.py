"""Alert domain entity — a detected suspicious behavior awaiting triage."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.domain.enums import (
    AlertCategory,
    AlertSource,
    AlertStatus,
    Severity,
)
from app.domain.exceptions import InvariantViolationError
from app.domain.value_objects.confidence import ConfidenceScore
from app.domain.value_objects.evidence import Evidence
from app.domain.value_objects.mitre import MitreTechnique

# Status values from which an alert is considered closed.
_CLOSED_STATUSES = {
    AlertStatus.RESOLVED,
    AlertStatus.FALSE_POSITIVE,
    AlertStatus.SUPPRESSED,
}


@dataclass(slots=True)
class Alert:
    """A detection finding with severity, confidence, evidence, and MITRE mapping."""

    id: UUID
    title: str
    description: str
    category: AlertCategory
    severity: Severity
    confidence: ConfidenceScore
    source: AlertSource
    status: AlertStatus = AlertStatus.NEW
    host: str | None = None
    user_principal: str | None = None
    explanation: str | None = None
    evidence: list[Evidence] = field(default_factory=list)
    techniques: list[MitreTechnique] = field(default_factory=list)
    assigned_to: UUID | None = None
    first_seen: datetime | None = None
    last_seen: datetime | None = None

    @property
    def is_closed(self) -> bool:
        return self.status in _CLOSED_STATUSES

    @property
    def is_ai_generated(self) -> bool:
        return self.source in (AlertSource.AI, AlertSource.HYBRID)

    def assign(self, user_id: UUID) -> None:
        if self.is_closed:
            raise InvariantViolationError("Cannot assign a closed alert")
        self.assigned_to = user_id
        if self.status == AlertStatus.NEW:
            self.status = AlertStatus.TRIAGING

    def close(self, *, status: AlertStatus) -> None:
        if status not in _CLOSED_STATUSES:
            raise InvariantViolationError(
                f"{status} is not a valid closing status"
            )
        self.status = status

    def validate_ai_evidence(self) -> None:
        """AI-generated alerts must cite at least one piece of evidence.

        This enforces the explainability guarantee described in the security model.
        """
        if self.is_ai_generated and not self.evidence:
            raise InvariantViolationError(
                "AI-generated alerts must include supporting evidence"
            )
