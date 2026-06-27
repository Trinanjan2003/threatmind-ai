"""Alert repository interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.alert import Alert
from app.domain.enums import AlertCategory, AlertStatus, Severity


@dataclass(slots=True)
class AlertFilter:
    status: AlertStatus | None = None
    severity: Severity | None = None
    category: AlertCategory | None = None
    host: str | None = None
    assigned_to: UUID | None = None
    query: str | None = None
    offset: int = 0
    limit: int = 25
    sort: str = "-created_at"


class AlertRepository(ABC):
    @abstractmethod
    async def get_by_id(self, alert_id: UUID) -> Alert | None: ...

    @abstractmethod
    async def search(self, flt: AlertFilter) -> tuple[list[Alert], int]:
        """Return (alerts, total_count)."""

    @abstractmethod
    async def add(self, alert: Alert) -> Alert: ...

    @abstractmethod
    async def update(self, alert: Alert) -> Alert: ...

    @abstractmethod
    async def count_by_status(self) -> dict[AlertStatus, int]: ...

    @abstractmethod
    async def count_by_severity(self) -> dict[Severity, int]: ...
