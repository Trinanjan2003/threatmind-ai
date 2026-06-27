"""Detection layer — rule engine that turns normalized events into alerts."""

from app.application.detection.engine import DetectionEngine
from app.application.detection.rules import DEFAULT_RULES, DetectionRule

__all__ = ["DEFAULT_RULES", "DetectionEngine", "DetectionRule"]
