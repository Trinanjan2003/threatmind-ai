"""Unit tests for the multi-agent hunt engine (with a fake LLM)."""

from __future__ import annotations

import pytest

from app.application.ports.llm import LLMMessage, LLMPort
from app.infrastructure.agents.engine import HuntEngine
from app.infrastructure.agents.state import Finding, HuntState


class _UnavailableLLM(LLMPort):
    """Simulates Ollama being down — exercises the heuristic fallback path."""

    async def complete(self, messages, *, temperature=None, max_tokens=None):  # type: ignore[override]
        raise RuntimeError("llm down")

    def stream(self, messages, *, temperature=None):  # type: ignore[override]
        raise RuntimeError("llm down")

    async def embed(self, texts):  # type: ignore[override]
        return [[0.0] for _ in texts]

    async def health(self) -> bool:
        return False


SAMPLE_EVENTS = [
    {
        "host": "WIN-001",
        "event_hash": "evt-1",
        "process": {"name": "powershell.exe", "command_line": "powershell.exe -enc ABCD"},
        "network": {"dst_ip": "185.234.219.10", "domain": "cdn-update-svc.top"},
    },
    {
        "host": "WIN-014",
        "event_hash": "evt-2",
        "process": {"name": "C:\\Windows\\Temp\\svc.exe", "command_line": "svc.exe", "hashes": {"sha256": "DEAD"}},
    },
]


@pytest.fixture
def engine() -> HuntEngine:
    return HuntEngine(llm=_UnavailableLLM(), search=None)


async def test_hunt_completes_and_produces_findings(engine: HuntEngine) -> None:
    state = HuntState(hunt_id="h1", query="find threats", focus="ransomware")
    state.events = list(SAMPLE_EVENTS)
    result = await engine.run(state)

    assert result.findings, "expected at least one finding"
    assert result.risk_score > 0
    assert result.summary
    assert result.report_markdown.startswith("# Incident Report")
    # All 8 agents should have been traced.
    assert len(result.agent_trace) == 8


async def test_threat_intel_flags_known_bad_indicator(engine: HuntEngine) -> None:
    state = HuntState(hunt_id="h2", query="q")
    state.events = list(SAMPLE_EVENTS)
    result = await engine.run(state)
    titles = " ".join(f.title for f in result.findings).lower()
    assert "malicious indicator" in titles or "correlated" in titles


async def test_detection_generated_during_hunt(engine: HuntEngine) -> None:
    state = HuntState(hunt_id="h3", query="q", focus="lotl")
    state.events = list(SAMPLE_EVENTS)
    result = await engine.run(state)
    # MITRE mapping + detection engineering should yield a rule when techniques exist.
    if result.technique_ids:
        assert result.detections
        assert result.detections[0]["format"] == "sigma"


async def test_evidence_guarantee_downgrades_unsupported_claims() -> None:
    state = HuntState(hunt_id="h4", query="q")
    state.add_finding(Finding(agent="x", title="claim", detail="no evidence", confidence=90))
    # Confidence capped because no evidence_refs were supplied.
    assert state.findings[0].confidence <= 20
