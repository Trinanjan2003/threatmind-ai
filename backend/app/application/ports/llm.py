"""LLM port — abstracts the (free, local) language-model provider.

The default adapter targets Ollama. Agents depend on this interface, never on a
concrete provider, per ADR 0002. No paid/hosted providers are permitted.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal

Role = Literal["system", "user", "assistant", "tool"]


@dataclass(slots=True)
class LLMMessage:
    role: Role
    content: str


class LLMPort(ABC):
    """Interface for text generation and embeddings via a local model."""

    @abstractmethod
    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Return a full completion for the given conversation."""

    @abstractmethod
    def stream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float | None = None,
    ) -> AsyncIterator[str]:
        """Yield completion tokens as they are produced."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return embedding vectors for the given texts."""

    @abstractmethod
    async def health(self) -> bool:
        """Return True if the model backend is reachable."""
