# ADR 0002 — Use Ollama (local) as the default, with a pluggable LLM port

**Status:** Accepted · **Date:** 2026-06-27

## Context
The platform requires LLM-powered multi-agent reasoning, but a hard project constraint is **no paid services and no payment integrations** — everything must be free and runnable locally on macOS, Windows, and Linux. We also want to avoid vendor lock-in and keep sensitive security telemetry on-premises.

## Decision
Default all AI inference to **Ollama**, a free, local LLM runtime, using open models (e.g. `llama3.1`, `qwen2.5`) and `nomic-embed-text` for embeddings. Access it through an abstract **LLM port** (`application/ports`) implemented by an `OllamaProvider` adapter. The port keeps room for other **free/local** runtimes later without touching agent code.

## Consequences
- ✅ Zero cost, no API keys, full data locality (security telemetry never leaves the host).
- ✅ Cross-platform; runs in Docker Compose or natively.
- ✅ Pluggable: agents depend on the port, not Ollama directly.
- ⚠️ Local model quality/latency depends on host hardware; we tune prompts and keep deterministic rule-based fallbacks.
- ⚠️ If Ollama is down, AI features degrade gracefully (rule-based only) rather than erroring.
- 🚫 We will **not** add hosted/paid providers (OpenAI, Anthropic API, etc.) — this contradicts the project's free/local mandate.
