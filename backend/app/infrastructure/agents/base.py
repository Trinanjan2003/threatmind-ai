"""BaseAgent — common scaffolding for all specialized agents.

Each agent gets the shared HuntState and an LLM port. Agents try to use the LLM
for reasoning; if it is unavailable they fall back to deterministic heuristics so
the hunt always completes with explainable output.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.ports.llm import LLMMessage, LLMPort
from app.core.logging import get_logger
from app.infrastructure.agents.state import HuntState

logger = get_logger(__name__)


class BaseAgent(ABC):
    name: str

    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

    async def run(self, state: HuntState) -> HuntState:
        state.agent_trace.append(self.name)
        try:
            return await self._execute(state)
        except Exception as exc:  # noqa: BLE001 - one agent must not crash a hunt
            logger.warning("agent_failed", agent=self.name, error=str(exc))
            return state

    @abstractmethod
    async def _execute(self, state: HuntState) -> HuntState: ...

    async def _llm_or_none(self, system: str, user: str) -> str | None:
        """Try the LLM; return None if unavailable so callers can fall back."""
        try:
            if not await self._llm.health():
                return None
            return await self._llm.complete(
                [LLMMessage(role="system", content=system), LLMMessage(role="user", content=user)]
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("llm_unavailable", agent=self.name, error=str(exc))
            return None
