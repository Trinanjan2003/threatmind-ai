"""ChatInvestigationUseCase — streaming, evidence-cited AI investigation.

Drives the agent collective for a natural-language question and yields a stream
of protocol events (agent steps, evidence, answer tokens) suitable for pushing
over a WebSocket. Falls back to a structured deterministic answer when the local
LLM is unavailable.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Literal

from app.application.ports.llm import LLMMessage, LLMPort
from app.application.ports.search import SearchPort
from app.core.logging import get_logger
from app.infrastructure.agents.engine import HuntEngine
from app.infrastructure.agents.state import HuntState

logger = get_logger(__name__)

EventType = Literal["agent_step", "evidence", "token", "done", "error"]


@dataclass(slots=True)
class ChatEvent:
    type: EventType
    data: dict[str, Any]


_SYSTEM_PROMPT = (
    "You are ThreatMind AI, a senior SOC analyst assistant. Answer the analyst's "
    "question using ONLY the provided findings and evidence. Be concise, precise, "
    "and cite hosts/techniques. Never invent facts not supported by evidence."
)


class ChatInvestigationUseCase:
    def __init__(self, *, llm: LLMPort, search: SearchPort | None = None) -> None:
        self._llm = llm
        self._search = search

    async def stream(self, question: str) -> AsyncIterator[ChatEvent]:
        hunt_id = f"chat_{uuid.uuid4().hex[:10]}"
        state = HuntState(hunt_id=hunt_id, query=question, focus=question)

        # Pull relevant events into context (best-effort).
        if self._search is not None:
            try:
                items, _ = await self._search.search_events(query=question, limit=50)
                state.events = items
            except Exception as exc:  # noqa: BLE001
                logger.debug("chat_event_search_failed", error=str(exc))

        # Run the agent collective to gather findings + evidence.
        engine = HuntEngine(llm=self._llm, search=self._search)
        try:
            state = await engine.run(state)
        except Exception as exc:  # noqa: BLE001
            yield ChatEvent("error", {"message": f"investigation failed: {exc}"})
            return

        # Emit agent steps.
        for agent in state.agent_trace:
            yield ChatEvent("agent_step", {"agent": agent, "status": "completed"})

        # Emit evidence citations.
        for finding in state.findings[:8]:
            for ref in finding.evidence_refs[:2]:
                yield ChatEvent("evidence", {"ref": ref, "summary": finding.title})

        # Stream the answer — via LLM if available, else a structured fallback.
        answer = await self._compose_answer(question, state)
        async for token in self._emit_tokens(question, state, answer):
            yield ChatEvent("token", {"content": token})

        yield ChatEvent("done", {"investigation_id": hunt_id, "risk_score": state.risk_score})

    async def _compose_answer(self, question: str, state: HuntState) -> str:
        findings_text = "\n".join(
            f"- [{f.severity}] {f.title}: {f.detail}" for f in state.findings
        )
        return (
            f"Question: {question}\n\nFindings:\n{findings_text or 'No notable findings.'}\n\n"
            f"Risk score: {state.risk_score}/100."
        )

    async def _emit_tokens(
        self, question: str, state: HuntState, context: str
    ) -> AsyncIterator[str]:
        # Try real streaming from the LLM first.
        try:
            if await self._llm.health():
                messages = [
                    LLMMessage(role="system", content=_SYSTEM_PROMPT),
                    LLMMessage(role="user", content=context),
                ]
                async for token in self._llm.stream(messages):
                    yield token
                return
        except Exception as exc:  # noqa: BLE001
            logger.debug("chat_stream_fallback", error=str(exc))

        # Deterministic fallback: stream the synthesized summary word-by-word.
        fallback = state.summary or (
            f"Based on the available telemetry, I found {len(state.findings)} findings "
            f"relevant to your question with an aggregate risk of {state.risk_score}/100. "
            f"Key techniques observed: {', '.join(sorted(state.technique_ids)) or 'none'}."
        )
        for word in fallback.split(" "):
            yield word + " "
