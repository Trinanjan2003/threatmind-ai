"""Integration test for the health API using an in-process ASGI client.

Marked 'integration' because the readiness probe touches infra clients. The
liveness probe and root work without any external services.
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
async def test_liveness_and_root() -> None:
    # Imported lazily so unit-test collection doesn't require the full app stack.
    import httpx
    from asgi_lifespan import LifespanManager

    from app.main import create_app

    app = create_app()
    async with LifespanManager(app), httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        live = await client.get("/api/v1/health/live")
        assert live.status_code == 200
        assert live.json()["status"] == "ok"

        root = await client.get("/")
        assert root.status_code == 200
        assert "ThreatMind" in root.json()["name"]


@pytest.mark.integration
async def test_protected_route_requires_auth() -> None:
    import httpx
    from asgi_lifespan import LifespanManager

    from app.main import create_app

    app = create_app()
    async with LifespanManager(app), httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v1/alerts")
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "UNAUTHENTICATED"
