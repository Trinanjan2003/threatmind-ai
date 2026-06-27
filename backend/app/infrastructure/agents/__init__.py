"""LangGraph multi-agent threat-hunting engine.

Eight specialized agents collaborate over a shared HuntState. The engine works
with a local Ollama model when available and degrades to deterministic heuristic
reasoning when the LLM is unreachable — so hunts always produce explainable,
evidence-backed findings.
"""

from app.infrastructure.agents.engine import HuntEngine
from app.infrastructure.agents.state import Finding, HuntState

__all__ = ["Finding", "HuntEngine", "HuntState"]
