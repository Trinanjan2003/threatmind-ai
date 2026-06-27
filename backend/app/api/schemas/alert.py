"""Alert API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.entities.alert import Alert
from app.domain.enums import AlertCategory, AlertSource, AlertStatus, Severity


class EvidenceSchema(BaseModel):
    summary: str
    event_id: str | None = None
    source: str | None = None
    fields: dict = Field(default_factory=dict)


class TechniqueSchema(BaseModel):
    technique_id: str
    name: str
    tactic: str
    url: str


class AlertResponse(BaseModel):
    id: UUID
    title: str
    description: str
    category: AlertCategory
    severity: Severity
    confidence: int
    confidence_label: str
    status: AlertStatus
    source: AlertSource
    host: str | None
    user_principal: str | None
    explanation: str | None
    evidence: list[EvidenceSchema]
    techniques: list[TechniqueSchema]
    assigned_to: UUID | None
    first_seen: datetime | None
    last_seen: datetime | None

    @classmethod
    def from_entity(cls, a: Alert) -> "AlertResponse":
        return cls(
            id=a.id,
            title=a.title,
            description=a.description,
            category=a.category,
            severity=a.severity,
            confidence=int(a.confidence),
            confidence_label=a.confidence.label,
            status=a.status,
            source=a.source,
            host=a.host,
            user_principal=a.user_principal,
            explanation=a.explanation,
            evidence=[EvidenceSchema(**e.to_dict()) for e in a.evidence],
            techniques=[
                TechniqueSchema(
                    technique_id=t.technique_id,
                    name=t.name,
                    tactic=t.tactic.value,
                    url=t.url,
                )
                for t in a.techniques
            ],
            assigned_to=a.assigned_to,
            first_seen=a.first_seen,
            last_seen=a.last_seen,
        )


class AlertUpdateRequest(BaseModel):
    status: AlertStatus | None = None
    assigned_to: UUID | None = None
