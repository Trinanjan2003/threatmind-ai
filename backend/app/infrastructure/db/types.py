"""Dialect-agnostic column types.

So the same models run on PostgreSQL (production) and SQLite (tests / portable
runs). On Postgres we use native ``JSONB`` / ``UUID``; on SQLite we fall back to
``JSON`` and ``CHAR(36)`` string UUIDs.
"""

from __future__ import annotations

import uuid

from sqlalchemy import CHAR, JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.types import TypeDecorator


class GUID(TypeDecorator[uuid.UUID]):
    """Platform-independent UUID: native ``UUID`` on Postgres, ``CHAR(36)`` else."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):  # type: ignore[no-untyped-def]
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):  # type: ignore[no-untyped-def]
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        return str(value)

    def process_result_value(self, value, dialect):  # type: ignore[no-untyped-def]
        if value is None:
            return None
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


# JSONB on Postgres, generic JSON elsewhere (SQLite stores as TEXT).
JSONType = JSON().with_variant(JSONB(), "postgresql")
