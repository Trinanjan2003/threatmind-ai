"""Local MITRE ATT&CK knowledge base (no external calls)."""

from app.infrastructure.mitre.knowledge_base import (
    MITRE_TECHNIQUES,
    get_technique,
    technique_value_object,
)

__all__ = ["MITRE_TECHNIQUES", "get_technique", "technique_value_object"]
