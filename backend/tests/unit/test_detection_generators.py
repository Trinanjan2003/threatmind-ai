"""Unit tests for detection content generators."""

from __future__ import annotations

import pytest

from app.domain.enums import DetectionFormat
from app.infrastructure.detections.generators import generate_detection


@pytest.mark.parametrize("fmt", [f.value for f in DetectionFormat])
def test_all_formats_generate_nonempty(fmt: str) -> None:
    content = generate_detection(fmt=fmt, technique_id="T1059.001", context="test")
    assert content.strip()


def test_sigma_contains_technique_tag() -> None:
    content = generate_detection(fmt="sigma", technique_id="T1059.001")
    assert "attack.t1059.001" in content
    assert "title:" in content


def test_yara_has_rule_block() -> None:
    content = generate_detection(fmt="yara", technique_id="T1003.001")
    assert content.startswith("rule ")
    assert "condition:" in content


def test_unknown_format_raises() -> None:
    with pytest.raises(ValueError):
        generate_detection(fmt="nope", technique_id="T1059.001")
