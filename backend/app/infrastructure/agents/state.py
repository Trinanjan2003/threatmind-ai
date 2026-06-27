"""Shared hunt state — the collaborative working memory for all agents.

Every agent reads from and appends to this object. It is serializable so it can
be persisted to Redis (keyed by hunt id), enabling resumable hunts and letting
agents read one another's outputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Finding:
    """A single agent finding. Must carry evidence to be accepted downstream."""

    agent: str
    title: str
    detail: str
    confidence: int
    severity: str = "medium"
    technique_ids: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "title": self.title,
            "detail": self.detail,
            "confidence": self.confidence,
            "severity": self.severity,
            "technique_ids": self.technique_ids,
            "evidence_refs": self.evidence_refs,
        }


@dataclass(slots=True)
class HuntState:
    """Mutable collaborative state passed between agents in the graph."""

    hunt_id: str
    query: str
    focus: str | None = None
    scope_hosts: list[str] = field(default_factory=list)

    # Collected context as agents run.
    events: list[dict[str, Any]] = field(default_factory=list)
    iocs: list[dict[str, Any]] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    technique_ids: set[str] = field(default_factory=set)

    # Outputs.
    risk_score: int = 0
    summary: str = ""
    report_markdown: str = ""
    detections: list[dict[str, str]] = field(default_factory=list)

    # Trace of which agents executed (for observability + audit).
    agent_trace: list[str] = field(default_factory=list)

    def add_finding(self, finding: Finding) -> None:
        """Append a finding, enforcing the evidence guarantee for AI claims."""
        if not finding.evidence_refs and finding.confidence > 0:
            # Keep explainability: unsupported claims are downgraded, not trusted.
            finding.confidence = min(finding.confidence, 20)
        self.findings.append(finding)
        self.technique_ids.update(finding.technique_ids)

    def to_dict(self) -> dict[str, Any]:
        return {
            "hunt_id": self.hunt_id,
            "query": self.query,
            "focus": self.focus,
            "scope_hosts": self.scope_hosts,
            "findings": [f.to_dict() for f in self.findings],
            "technique_ids": sorted(self.technique_ids),
            "risk_score": self.risk_score,
            "summary": self.summary,
            "report_markdown": self.report_markdown,
            "detections": self.detections,
            "agent_trace": self.agent_trace,
        }
