"""Attack-timeline reconstruction.

Given a set of alerts (or normalized events), order them along the MITRE kill
chain to produce a coherent attack narrative. Pure logic — testable without I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.entities.alert import Alert
from app.domain.enums import MitreTactic
from app.infrastructure.mitre.knowledge_base import get_technique

# Canonical ordering of tactics along the kill chain.
_TACTIC_ORDER: dict[MitreTactic, int] = {
    MitreTactic.INITIAL_ACCESS: 0,
    MitreTactic.EXECUTION: 1,
    MitreTactic.PERSISTENCE: 2,
    MitreTactic.PRIVILEGE_ESCALATION: 3,
    MitreTactic.DEFENSE_EVASION: 4,
    MitreTactic.CREDENTIAL_ACCESS: 5,
    MitreTactic.DISCOVERY: 6,
    MitreTactic.LATERAL_MOVEMENT: 7,
    MitreTactic.COLLECTION: 8,
    MitreTactic.COMMAND_AND_CONTROL: 9,
    MitreTactic.EXFILTRATION: 10,
    MitreTactic.IMPACT: 11,
}


@dataclass(slots=True)
class TimelineStep:
    phase: str
    title: str
    description: str
    occurred_at: datetime | None
    technique_id: str | None = None
    host: str | None = None
    order_index: int = 0
    evidence_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "phase": self.phase,
            "title": self.title,
            "description": self.description,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
            "technique_id": self.technique_id,
            "host": self.host,
            "order_index": self.order_index,
            "evidence_refs": self.evidence_refs,
        }


def reconstruct_timeline(alerts: list[Alert]) -> list[TimelineStep]:
    """Order alerts into a kill-chain timeline.

    Primary sort is the MITRE tactic phase; ties break by timestamp. This yields
    a readable Initial Access → … → Impact narrative even when event timestamps
    are close together.
    """
    steps: list[TimelineStep] = []
    for alert in alerts:
        # Choose the most kill-chain-advanced technique on the alert.
        best_tactic: MitreTactic | None = None
        best_tid: str | None = None
        for tech in alert.techniques:
            rec = get_technique(tech.technique_id)
            if rec is None:
                continue
            if best_tactic is None or _TACTIC_ORDER.get(rec.tactic, 99) < _TACTIC_ORDER.get(best_tactic, 99):
                best_tactic = rec.tactic
                best_tid = tech.technique_id
        phase = best_tactic.value if best_tactic else "execution"
        steps.append(
            TimelineStep(
                phase=phase,
                title=alert.title,
                description=alert.explanation or alert.description,
                occurred_at=alert.first_seen,
                technique_id=best_tid,
                host=alert.host,
                evidence_refs=[e.event_id for e in alert.evidence if e.event_id],
            )
        )

    def _key(s: TimelineStep) -> tuple[int, float]:
        tactic = next((t for t in MitreTactic if t.value == s.phase), None)
        order = _TACTIC_ORDER.get(tactic, 99) if tactic else 99
        ts = s.occurred_at.timestamp() if s.occurred_at else 0.0
        return (order, ts)

    steps.sort(key=_key)
    for i, step in enumerate(steps):
        step.order_index = i
    return steps
