"""Shared pytest fixtures.

Unit tests (``tests/unit``) require no I/O. Integration tests use the Postgres
and Redis services from docker-compose / CI. Set ``DATABASE_URL`` to point at a
disposable test database before running integration tests.
"""

from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"
