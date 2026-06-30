"""Cover the RunHuntUseCase orchestration and CloudTrail parser edge cases."""

from __future__ import annotations

import json

import pytest

from app.application.investigation.run_hunt import RunHuntUseCase
from app.application.ports.llm import LLMPort
from app.infrastructure.agents.engine import HuntEngine
from app.infrastructure.parsers import CloudTrailParser


class _DownLLM(LLMPort):
    async def complete(self, messages, *, temperature=None, max_tokens=None):  # type: ignore[override]
        raise RuntimeError("down")

    def stream(self, messages, *, temperature=None):  # type: ignore[override]
        raise RuntimeError("down")

    async def embed(self, texts):  # type: ignore[override]
        return [[0.0] for _ in texts]

    async def health(self) -> bool:
        return False


class _FakeCache:
    def __init__(self) -> None:
        self.stored: dict[str, str] = {}

    async def get(self, key: str): return self.stored.get(key)  # noqa: E704
    async def set(self, key, value, *, ttl_seconds=None): self.stored[key] = value  # noqa: E704
    async def delete(self, key): self.stored.pop(key, None)  # noqa: E704
    async def incr(self, key, *, ttl_seconds=None): return 1  # noqa: E704
    async def publish(self, channel, message): ...  # noqa: E704
    def subscribe(self, channel): ...  # noqa: E704
    async def health(self): return True  # noqa: E704


@pytest.mark.unit
async def test_run_hunt_persists_state_to_cache() -> None:
    cache = _FakeCache()
    engine = HuntEngine(llm=_DownLLM(), search=None)
    uc = RunHuntUseCase(engine=engine, cache=cache)  # type: ignore[arg-type]
    state = await uc.execute(hunt_id="h1", query="find threats", focus="ransomware")

    assert state.hunt_id == "h1"
    assert len(state.agent_trace) == 8  # all agents ran via fallback
    # The hunt state was cached as JSON.
    assert "hunt:h1" in cache.stored
    cached = json.loads(cache.stored["hunt:h1"])
    assert cached["hunt_id"] == "h1"


@pytest.mark.unit
async def test_run_hunt_without_cache() -> None:
    engine = HuntEngine(llm=_DownLLM(), search=None)
    uc = RunHuntUseCase(engine=engine, cache=None)
    state = await uc.execute(hunt_id="h2", query="q")
    assert state.hunt_id == "h2"


@pytest.mark.unit
class TestCloudTrailEdges:
    def test_records_envelope_with_error_event(self) -> None:
        payload = {
            "Records": [
                {
                    "eventTime": "2026-06-27T09:30:00Z",
                    "eventSource": "signin.amazonaws.com",
                    "eventName": "ConsoleLogin",
                    "errorCode": "Failed authentication",
                    "userIdentity": {"userName": "x"},
                    "readOnly": False,
                }
            ]
        }
        result = CloudTrailParser().parse(json.dumps(payload))
        ev = result.events[0]
        assert "api_error" in ev.tags
        assert "mutating" in ev.tags

    def test_bare_array(self) -> None:
        payload = [{"eventTime": "2026-06-27T09:30:00Z", "eventSource": "s3.amazonaws.com", "eventName": "GetObject"}]
        result = CloudTrailParser().parse(json.dumps(payload))
        assert len(result.events) == 1

    def test_invalid_json(self) -> None:
        result = CloudTrailParser().parse("{bad")
        assert result.errors and not result.events

    def test_empty(self) -> None:
        assert CloudTrailParser().parse("").total == 0
