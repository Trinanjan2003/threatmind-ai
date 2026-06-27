# ADR 0001 — Adopt Clean Architecture for the backend

**Status:** Accepted · **Date:** 2026-06-27

## Context
ThreatMind AI must integrate many volatile external systems (Postgres, Redis, Elasticsearch, Ollama, LangGraph, multiple log parsers) and is expected to grow for years. We need the core security logic to remain testable and stable as these details change.

## Decision
Use Clean Architecture (Ports & Adapters). The `domain` layer is pure (no framework/I/O imports) and defines repository interfaces. The `application` layer holds use cases and depends only on domain interfaces and `application/ports`. The `infrastructure` layer implements those interfaces (DB, search, cache, LLM, parsers, agents). The `api` layer (FastAPI) depends on application use cases. Concrete adapters are bound in a DI container at startup.

## Consequences
- ✅ Domain + application logic is unit-testable with fakes, no DB/network needed → supports the 80% coverage target.
- ✅ Swapping an adapter (e.g. a different free LLM runtime, or OpenSearch for Elasticsearch) doesn't touch business rules.
- ✅ Clear dependency rule prevents framework leakage into core logic.
- ⚠️ More upfront boilerplate (interfaces + DI wiring) and indirection. Accepted as the cost of long-term maintainability for an enterprise platform.
