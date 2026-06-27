"""Unit tests for domain value objects (pure, no I/O)."""

from __future__ import annotations

import pytest

from app.domain.enums import MitreTactic
from app.domain.exceptions import InvariantViolationError
from app.domain.value_objects.confidence import ConfidenceScore
from app.domain.value_objects.mitre import MitreTechnique


class TestConfidenceScore:
    @pytest.mark.parametrize(
        ("value", "label"),
        [(95, "very_high"), (70, "high"), (50, "medium"), (25, "low"), (5, "very_low")],
    )
    def test_label_buckets(self, value: int, label: str) -> None:
        assert ConfidenceScore(value).label == label

    @pytest.mark.parametrize("value", [-1, 101, 200])
    def test_out_of_range_rejected(self, value: int) -> None:
        with pytest.raises(InvariantViolationError):
            ConfidenceScore(value)

    def test_int_cast(self) -> None:
        assert int(ConfidenceScore(42)) == 42


class TestMitreTechnique:
    def test_valid_technique(self) -> None:
        t = MitreTechnique("T1059", "Command Interpreter", MitreTactic.EXECUTION)
        assert not t.is_subtechnique
        assert t.url.endswith("/T1059/")

    def test_subtechnique(self) -> None:
        t = MitreTechnique("T1059.001", "PowerShell", MitreTactic.EXECUTION)
        assert t.is_subtechnique
        assert t.parent_id == "T1059"
        assert t.url.endswith("/T1059/001/")

    @pytest.mark.parametrize("bad_id", ["X1059", "1059", "T105", "T1059.1"])
    def test_invalid_id_rejected(self, bad_id: str) -> None:
        with pytest.raises(InvariantViolationError):
            MitreTechnique(bad_id, "x", MitreTactic.EXECUTION)
