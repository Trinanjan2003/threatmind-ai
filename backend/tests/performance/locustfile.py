"""Performance scenarios (Locust). Run against a live stack:

    locust -f tests/performance/locustfile.py --host http://localhost:8000

Targets (see docs/01-prd.md NFRs): P95 < 300ms for interactive endpoints.
"""

from __future__ import annotations

try:
    from locust import HttpUser, between, task
except ImportError:  # locust is an optional, on-demand dependency
    HttpUser = object  # type: ignore[assignment,misc]

    def task(fn):  # type: ignore[no-redef]
        return fn

    def between(a, b):  # type: ignore[no-redef]
        return None


class SocAnalyst(HttpUser):  # type: ignore[misc]
    wait_time = between(1, 3)

    @task(3)
    def health(self) -> None:
        self.client.get("/api/v1/health/live")

    @task(2)
    def supported_sources(self) -> None:
        self.client.get("/api/v1/ingest/supported")

    @task(1)
    def mitre_matrix(self) -> None:
        self.client.get("/api/v1/mitre/matrix")
