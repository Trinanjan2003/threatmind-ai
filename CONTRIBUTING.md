# Contributing to ThreatMind AI

Thanks for your interest! This project is built with free, open-source software
and runs locally (Ollama for AI). Please keep contributions aligned with that
principle — **no paid services or payment integrations**.

## Getting started

See [`docs/11-deployment-guide.md`](docs/11-deployment-guide.md) for local setup
(Docker Compose or native). The repo layout is documented in
[`docs/05-folder-structure.md`](docs/05-folder-structure.md).

## Ground rules

- **Architecture:** respect the Clean Architecture dependency rule — the
  `domain` layer imports no frameworks; adapters live in `infrastructure`.
- **Tests:** add unit tests for new logic; keep coverage ≥ 80%. See
  [`docs/10-test-plan.md`](docs/10-test-plan.md).
- **Style:** Python via `ruff` + `mypy`; TypeScript via ESLint + `tsc`.
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`…).
- **Security:** never commit secrets; validate all input; parameterized queries
  and structured search queries only.

## Quality gate (run before opening a PR)

```bash
# backend
cd backend && ruff check . && ruff format --check . && mypy app && pytest --cov=app

# frontend
cd frontend && npm run lint && npm run typecheck && npm run build
```

CI (`.github/workflows/ci.yml`) enforces these on every PR.

## Adding a data-source parser

Implement `LogParser` in `backend/app/infrastructure/parsers/`, register it in
`registry.py`, and add unit tests with a sample payload. The normalized schema
is `app/domain/events/normalized_event.py`.
