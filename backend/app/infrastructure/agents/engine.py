"""HuntEngine — orchestrates the specialized agents over a shared HuntState.

When LangGraph is installed, the agents are wired into a StateGraph with the
Orchestrator routing the flow. When it is not (or to keep things lightweight),
the same agents run through a deterministic sequential pipeline. Either way the
collaboration contract — shared state, evidence-cited findings — is identical.
"""

from __future__ import annotations

from app.application.ports.llm import LLMPort
from app.application.ports.search import SearchPort
from app.core.logging import get_logger
from app.infrastructure.agents.specialized import AGENT_CLASSES
from app.infrastructure.agents.state import HuntState

logger = get_logger(__name__)

try:  # LangGraph is optional; the engine works without it.
    from langgraph.graph import END, StateGraph  # type: ignore

    _LANGGRAPH_AVAILABLE = True
except Exception:  # noqa: BLE001 - absence is a supported configuration
    _LANGGRAPH_AVAILABLE = False


class HuntEngine:
    def __init__(self, *, llm: LLMPort, search: SearchPort | None = None) -> None:
        self._llm = llm
        self._search = search
        self._agents = [cls(llm) for cls in AGENT_CLASSES]

    @property
    def uses_langgraph(self) -> bool:
        return _LANGGRAPH_AVAILABLE

    async def _gather_events(self, state: HuntState) -> None:
        """Populate state.events from the search store for the hunt scope."""
        if self._search is None:
            return
        try:
            for host in state.scope_hosts or [None]:  # type: ignore[list-item]
                items, _ = await self._search.search_events(
                    query=state.focus, host=host, limit=100
                )
                state.events.extend(items)
        except Exception as exc:  # noqa: BLE001
            logger.warning("hunt_event_gather_failed", error=str(exc))

    async def run(self, state: HuntState) -> HuntState:
        await self._gather_events(state)
        if _LANGGRAPH_AVAILABLE:
            return await self._run_langgraph(state)
        return await self._run_sequential(state)

    async def _run_sequential(self, state: HuntState) -> HuntState:
        """Deterministic pipeline — the always-available execution path."""
        for agent in self._agents:
            state = await agent.run(state)
        return state

    async def _run_langgraph(self, state: HuntState) -> HuntState:
        """Graph-based execution using LangGraph when present."""
        try:
            graph = StateGraph(dict)

            # Wrap each agent as a graph node operating on a dict carrier.
            def make_node(agent):  # type: ignore[no-untyped-def]
                async def _node(carrier: dict) -> dict:
                    st: HuntState = carrier["state"]
                    carrier["state"] = await agent.run(st)
                    return carrier

                return _node

            prev: str | None = None
            for agent in self._agents:
                graph.add_node(agent.name, make_node(agent))
                if prev is None:
                    graph.set_entry_point(agent.name)
                else:
                    graph.add_edge(prev, agent.name)
                prev = agent.name
            if prev is not None:
                graph.add_edge(prev, END)

            compiled = graph.compile()
            result = await compiled.ainvoke({"state": state})
            return result["state"]
        except Exception as exc:  # noqa: BLE001 - fall back if graph wiring fails
            logger.warning("langgraph_failed_fallback_sequential", error=str(exc))
            return await self._run_sequential(state)
