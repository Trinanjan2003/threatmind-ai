"""Audit log repository interface (append-only)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(slots=True)
class AuditEntry:
    actor_id: UUID | None
    actor_label: str | None
    action: str
    resource_type: str
    resource_id: str | None
    status: str = "success"
    ip: str | None = None
    user_agent: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AuditLogRepository(ABC):
    """Append-only. No update or delete operations are defined by design."""

    @abstractmethod
    async def record(self, entry: AuditEntry) -> None: ...

    @abstractmethod
    async def query(
        self, *, actor_id: UUID | None = None, action: str | None = None,
        offset: int = 0, limit: int = 50,
    ) -> tuple[list[dict[str, Any]], int]: ...
