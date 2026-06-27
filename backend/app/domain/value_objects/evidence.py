"""Evidence value object — a citation linking a finding to a concrete event."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Evidence:
    """A single piece of supporting evidence for a finding.

    ``event_id`` references a normalized event stored in Elasticsearch. Every
    AI-produced finding must carry at least one Evidence item — this is the
    guardrail that keeps conclusions explainable and auditable.
    """

    summary: str
    event_id: str | None = None
    source: str | None = None
    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "event_id": self.event_id,
            "source": self.source,
            "fields": self.fields,
        }
