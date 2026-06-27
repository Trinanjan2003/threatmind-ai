# ThreatMind AI — Folder Structure & Conventions

This monorepo is organized by deployable unit at the top level, and by **Clean Architecture layer** within the backend.

```
threatmind-ai/
├── README.md
├── LICENSE                      # Apache 2.0
├── .env.example                 # all config; copy to .env
├── .editorconfig
├── .gitignore
├── Makefile                     # dev tasks (macOS/Linux)
├── docker-compose.yml           # full local stack
├── docs/                        # ← architecture & product docs (this folder)
│   ├── 00-roadmap.md
│   ├── 01-prd.md
│   ├── 02-system-architecture.md
│   ├── 03-database-schema.md
│   ├── 04-api-design.md
│   ├── 05-folder-structure.md
│   ├── 06-security-model.md
│   ├── 11-deployment-guide.md
│   └── adr/                     # architecture decision records
│
├── scripts/
│   └── dev.ps1                  # dev tasks (Windows / PowerShell)
│
├── backend/                     # ← FastAPI service (Clean Architecture)
│   ├── pyproject.toml           # deps + tool config (ruff, mypy, pytest)
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── app/
│   │   ├── main.py              # FastAPI app factory + lifespan
│   │   ├── container.py         # DI container (wires ports → adapters)
│   │   │
│   │   ├── core/                # cross-cutting (framework-agnostic-ish)
│   │   │   ├── config.py        # Pydantic Settings
│   │   │   ├── logging.py       # structured logging setup
│   │   │   ├── security.py      # hashing, JWT encode/decode, encryption
│   │   │   ├── errors.py        # domain→HTTP error mapping, error envelope
│   │   │   └── observability.py # Prometheus + OTel setup
│   │   │
│   │   ├── domain/              # ⬅ INNERMOST. Pure. No framework imports.
│   │   │   ├── entities/        # User, Alert, Incident, IOC, Investigation…
│   │   │   ├── value_objects/   # Severity, Confidence, MitreTechnique…
│   │   │   ├── events/          # NormalizedEvent schema, domain events
│   │   │   ├── enums.py         # AlertCategory, Role, etc.
│   │   │   ├── exceptions.py    # domain exceptions
│   │   │   └── repositories/    # repository INTERFACES (ports)
│   │   │
│   │   ├── application/         # use cases / services + ports
│   │   │   ├── auth/            # login, mfa, refresh, rbac use cases
│   │   │   ├── ingestion/       # ingest_file, normalize use cases
│   │   │   ├── detection/       # run_rules, score, create_alert
│   │   │   ├── investigation/   # run_hunt, chat, triage orchestration
│   │   │   ├── detections/      # rule/query generation use cases
│   │   │   ├── reporting/       # report + timeline generation
│   │   │   ├── dto.py           # request/response DTOs (internal)
│   │   │   └── ports/           # LLM, search, cache, bus interfaces
│   │   │
│   │   ├── infrastructure/      # ⬅ OUTERMOST adapters (implement ports)
│   │   │   ├── db/
│   │   │   │   ├── session.py   # async engine/session
│   │   │   │   ├── models/      # SQLAlchemy ORM models
│   │   │   │   └── repositories/# repository IMPLEMENTATIONS
│   │   │   ├── search/          # Elasticsearch client + queries
│   │   │   ├── cache/           # Redis cache + pub/sub bus
│   │   │   ├── llm/             # Ollama provider (implements LLM port)
│   │   │   ├── parsers/         # one module per data source
│   │   │   │   ├── base.py      # LogParser interface
│   │   │   │   ├── sysmon.py
│   │   │   │   ├── cloudtrail.py
│   │   │   │   └── …            # windows_event, zeek, suricata, …
│   │   │   ├── agents/          # LangGraph agents + graph
│   │   │   │   ├── graph.py     # orchestrator graph definition
│   │   │   │   ├── state.py     # HuntState (shared memory)
│   │   │   │   ├── base.py      # BaseAgent
│   │   │   │   ├── threat_intel.py
│   │   │   │   ├── ioc_correlation.py
│   │   │   │   ├── log_investigation.py
│   │   │   │   ├── malware_analysis.py
│   │   │   │   ├── mitre_mapping.py
│   │   │   │   ├── risk_scoring.py
│   │   │   │   ├── reporting.py
│   │   │   │   └── detection_engineering.py
│   │   │   ├── detections/      # Sigma/YARA/Suricata/SPL/KQL generators
│   │   │   └── mitre/           # local ATT&CK knowledge base loader
│   │   │
│   │   ├── api/                 # FastAPI adapter layer
│   │   │   ├── deps.py          # auth/rbac dependencies, DI accessors
│   │   │   ├── middleware/      # request-id, rate-limit, audit, errors
│   │   │   ├── schemas/         # Pydantic request/response models
│   │   │   └── v1/
│   │   │       ├── router.py    # aggregates all v1 routers
│   │   │       └── routes/      # auth.py, alerts.py, hunts.py, chat.py…
│   │   │
│   │   ├── data/                # seed data (roles, MITRE reference)
│   │   └── scripts/             # seed.py, maintenance scripts
│   │
│   └── tests/
│       ├── unit/                # domain + application (no I/O)
│       ├── integration/         # repositories, parsers, API w/ test DB
│       ├── e2e/                 # full-stack flows
│       ├── security/            # authz, rate-limit, injection tests
│       ├── performance/         # load/latency (locust/k6)
│       ├── factories/           # test data factories
│       └── conftest.py
│
├── frontend/                    # ← Next.js 14 app (added in Phase 1)
│   ├── package.json
│   ├── next.config.mjs
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── Dockerfile
│   ├── public/
│   └── src/
│       ├── app/                 # App Router routes
│       │   ├── (auth)/login/
│       │   └── (dashboard)/     # dashboard, alerts, incidents, hunts,
│       │       │               #   mitre, timeline, detections, chat, admin
│       │       └── layout.tsx
│       ├── components/
│       │   ├── ui/              # shadcn primitives
│       │   ├── charts/          # Recharts wrappers
│       │   ├── layout/          # sidebar, topbar, theme toggle
│       │   └── features/        # alert table, mitre matrix, timeline…
│       ├── lib/                 # api client, auth, utils, query client
│       ├── hooks/
│       ├── stores/              # client state (zustand)
│       └── styles/              # globals.css, design tokens
│
└── infra/
    ├── docker/                  # service Dockerfiles & configs
    │   ├── prometheus.yml
    │   └── grafana/
    └── k8s/                     # Kubernetes manifests / kustomize
        ├── base/
        └── overlays/{dev,staging,prod}/
```

## Naming & code conventions

**Python (backend)**
- `snake_case` modules/functions, `PascalCase` classes, `UPPER_SNAKE` constants.
- Domain layer imports **nothing** from `infrastructure`/`api`/frameworks.
- Repository interfaces live in `domain/repositories`; implementations in `infrastructure/db/repositories`.
- Ports (LLM/search/cache/bus) in `application/ports`; adapters in `infrastructure/*`.
- Type hints everywhere; `mypy` clean. Format/lint with `ruff`.
- One use case per file where practical; use cases are classes with an `execute()` (or `__call__`) method and constructor-injected dependencies.

**TypeScript (frontend)**
- `PascalCase` components, `camelCase` functions/vars, colocated component + styles.
- Server Components by default; `"use client"` only where interactivity is needed.
- API access through a single typed client in `lib/api`.

**Tests**
- Mirror source tree under `tests/`. Unit tests never touch I/O (use fakes/mocks of ports). Integration tests use ephemeral Postgres/ES via Docker or testcontainers.

**Commits & branches**
- Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`). Feature branches off `main`; PRs run the CI gate (lint, type, test, coverage).
