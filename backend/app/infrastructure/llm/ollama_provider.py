"""Ollama LLM provider — the default (free, local) implementation of LLMPort.

Talks to a local Ollama server over HTTP. No API keys, no paid services.
Gracefully reports unavailability via ``health()`` so the app can degrade to
rule-based-only operation when Ollama is not running.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from app.application.ports.llm import LLMMessage, LLMPort
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OllamaProvider(LLMPort):
    def __init__(
        self,
        *,
        base_url: str | None = None,
        model: str | None = None,
        embedding_model: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self._base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self._model = model or settings.ollama_model
        self._embedding_model = embedding_model or settings.ollama_embedding_model
        self._timeout = timeout or settings.llm_request_timeout

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout)

    @staticmethod
    def _to_payload(messages: list[LLMMessage]) -> list[dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in messages]

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        body = {
            "model": self._model,
            "messages": self._to_payload(messages),
            "stream": False,
            "options": {
                "temperature": (
                    temperature if temperature is not None else settings.llm_temperature
                ),
                **({"num_predict": max_tokens} if max_tokens else {}),
            },
        }
        async with self._client() as client:
            resp = await client.post("/api/chat", json=body)
            resp.raise_for_status()
            data = resp.json()
        return str(data.get("message", {}).get("content", ""))

    async def stream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float | None = None,
    ) -> AsyncIterator[str]:
        body = {
            "model": self._model,
            "messages": self._to_payload(messages),
            "stream": True,
            "options": {
                "temperature": (
                    temperature if temperature is not None else settings.llm_temperature
                )
            },
        }
        async with self._client() as client, client.stream(
            "POST", "/api/chat", json=body
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:  # pragma: no cover - defensive
                    continue
                token = chunk.get("message", {}).get("content")
                if token:
                    yield token
                if chunk.get("done"):
                    break

    async def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        async with self._client() as client:
            for text in texts:
                resp = await client.post(
                    "/api/embeddings",
                    json={"model": self._embedding_model, "prompt": text},
                )
                resp.raise_for_status()
                vectors.append(resp.json().get("embedding", []))
        return vectors

    async def health(self) -> bool:
        try:
            async with self._client() as client:
                resp = await client.get("/api/tags")
                return resp.status_code == 200
        except (httpx.HTTPError, OSError) as exc:
            logger.warning("ollama_health_check_failed", error=str(exc))
            return False
