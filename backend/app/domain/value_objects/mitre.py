"""MITRE ATT&CK technique value object."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.enums import MitreTactic
from app.domain.exceptions import InvariantViolationError

# Matches techniques (T1059) and sub-techniques (T1059.001).
_TECHNIQUE_ID_RE = re.compile(r"^T\d{4}(\.\d{3})?$")


@dataclass(frozen=True, slots=True)
class MitreTechnique:
    """A reference to a MITRE ATT&CK technique or sub-technique."""

    technique_id: str
    name: str
    tactic: MitreTactic

    def __post_init__(self) -> None:
        if not _TECHNIQUE_ID_RE.match(self.technique_id):
            raise InvariantViolationError(
                f"Invalid MITRE technique id: {self.technique_id!r}"
            )

    @property
    def is_subtechnique(self) -> bool:
        return "." in self.technique_id

    @property
    def parent_id(self) -> str:
        return self.technique_id.split(".", 1)[0]

    @property
    def url(self) -> str:
        path = self.technique_id.replace(".", "/")
        return f"https://attack.mitre.org/techniques/{path}/"
