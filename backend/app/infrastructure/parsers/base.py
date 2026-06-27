"""LogParser interface and shared parsing helpers.

Each data source provides a parser that turns raw exported logs into a list of
``NormalizedEvent`` objects. Parsers are pure (no I/O) so they are unit-testable
and reusable across upload and connector ingestion paths.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.domain.enums import DataSourceType
from app.domain.events.normalized_event import NormalizedEvent


@dataclass(slots=True)
class ParseResult:
    events: list[NormalizedEvent] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.events) + len(self.errors)


class LogParser(ABC):
    """Transforms raw source records into normalized events."""

    source_type: DataSourceType

    @abstractmethod
    def parse(self, raw: str | bytes) -> ParseResult:
        """Parse a raw log payload (file contents) into normalized events."""

    # ── Shared helpers ──
    @staticmethod
    def parse_timestamp(value: Any) -> datetime:
        """Best-effort timestamp parsing; falls back to now() on failure."""
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=UTC)
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=UTC)
        if isinstance(value, str):
            text = value.strip().replace("Z", "+00:00")
            for fmt in (None,):  # try fromisoformat first
                try:
                    dt = datetime.fromisoformat(text)
                    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
                except ValueError:
                    break
            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%m/%d/%Y %I:%M:%S %p",
                "%b %d %H:%M:%S",
            ):
                try:
                    dt = datetime.strptime(text, fmt)  # noqa: DTZ007
                    return dt.replace(tzinfo=UTC)
                except ValueError:
                    continue
        return datetime.now(UTC)
