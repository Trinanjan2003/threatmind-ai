"""RunHuntUseCase — launches an autonomous multi-agent hunt.

Builds the initial HuntState, runs it through the HuntEngine, optionally persists
agent memory to the cache, and returns the resulting state. Pure orchestration —
no HTTP knowledge.
"""

from __future__ import annotations

import json

from app.application.ports.cache import CachePort
from app.core.logging import get_logger
from app.infrastructure.agents.engine import HuntEngine
from app.infrastructure.agents.state import HuntState

logger = get_logger(__name__)


class RunHuntUseCase:
    def __init__(self, *, engine: HuntEngine, cache: CachePort | None = None) -> None:
        self._engine = engine
        self._cache = cache

    async def execute(
        self,
        *,
        hunt_id: str,
        query: str,
        focus: str | None = None,
        scope_hosts: list[str] | None = None,
    ) -> HuntState:
        state = HuntState(
            hunt_id=hunt_id,
            query=query,
            focus=focus,
            scope_hosts=scope_hosts or [],
        )
        logger.info("hunt_started", hunt_id=hunt_id, focus=focus, langgraph=self._engine.uses_langgraph)
        state = await self._engine.run(state)

        # Persist the hunt state to cache (agent memory / resumability).
        if self._cache is not None:
            try:
                await self._cache.set(
                    f"hunt:{hunt_id}", json.dumps(state.to_dict()), ttl_seconds=86400
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("hunt_state_persist_failed", error=str(exc))

        logger.info("hunt_complete", hunt_id=hunt_id, findings=len(state.findings), risk=state.risk_score)
        return state
