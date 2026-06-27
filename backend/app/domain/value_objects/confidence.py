"""Confidence score value object (0–100)."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.exceptions import InvariantViolationError


@dataclass(frozen=True, slots=True)
class ConfidenceScore:
    """A bounded confidence score in the inclusive range [0, 100]."""

    value: int

    def __post_init__(self) -> None:
        if not 0 <= self.value <= 100:
            raise InvariantViolationError(
                f"Confidence must be between 0 and 100, got {self.value}"
            )

    @property
    def label(self) -> str:
        if self.value >= 85:
            return "very_high"
        if self.value >= 65:
            return "high"
        if self.value >= 40:
            return "medium"
        if self.value >= 20:
            return "low"
        return "very_low"

    def __int__(self) -> int:
        return self.value
