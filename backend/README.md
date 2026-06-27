# ThreatMind AI — Backend

FastAPI service built with Clean Architecture. See [`../docs`](../docs) for the
full design (architecture, DB schema, API, security model).

## Layout

```
app/
  core/            cross-cutting: config, logging, security, errors, observability
  domain/          pure business rules (entities, value objects, enums, repo interfaces)
  application/     use cases + ports (LLM/cache/search)
  infrastructure/  adapters: SQLAlchemy repos, Redis, Elasticsearch, Ollama, parsers, agents
  api/             FastAPI routers, schemas, middleware, deps
  scripts/         seed + maintenance
```

The dependency rule: `domain` ← `application` ← `infrastructure`/`api`. The
domain layer imports no framework or I/O code. Concrete adapters are wired in
`app/container.py` (the composition root).

## Develop

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# Infra (from repo root):  docker compose up -d postgres redis elasticsearch
alembic upgrade head
python -m app.scripts.seed
uvicorn app.main:app --reload
```

API docs at http://localhost:8000/docs.

## Quality gates

```bash
ruff check . && ruff format --check .   # lint + format
mypy app                                # types
pytest --cov=app --cov-report=term-missing   # tests + coverage (≥80%)
bandit -r app -ll                       # security scan
```

> Requires **Python 3.11+** (uses `StrEnum`, `datetime.UTC`, modern typing).

## AI / LLM

All inference is local via **Ollama** (free). Configure `OLLAMA_BASE_URL` and
`OLLAMA_MODEL` in `.env`. If Ollama is unavailable, AI features degrade
gracefully and the rest of the API keeps working.
