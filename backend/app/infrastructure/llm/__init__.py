"""LLM adapters. Default: Ollama (free, local)."""

from app.infrastructure.llm.ollama_provider import OllamaProvider

__all__ = ["OllamaProvider"]
