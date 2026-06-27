# ThreatMind AI — System Architecture

**Status:** Living document · **Owner:** Architecture · **Audience:** Engineering

---

## 1. Architectural overview

ThreatMind AI follows **Clean Architecture** (a.k.a. Hexagonal / Ports & Adapters). Dependencies point inward: the domain knows nothing about FastAPI, SQLAlchemy, Redis, Elasticsearch, or Ollama. Those are details plugged in at the edges through interfaces (ports) defined by the inner layers.

```
        ┌───────────────────────────────────────────────┐
        │                   API / Adapters                │  ← FastAPI routers, schemas,
        │  (HTTP, WebSocket, CLI, background workers)      │    deps, middleware
        ├───────────────────────────────────────────────┤
        │                  Application Layer               │  ← use cases / services,
        │   (orchestration, DTOs, ports, unit-of-work)     │    DI wiring
        ├───────────────────────────────────────────────┤
        │                    Domain Layer                  │  ← entities, value objects,
        │   (pure business rules, no I/O, no frameworks)   │    domain events, interfaces
        ├───────────────────────────────────────────────┤
        │                Infrastructure Layer              │  ← repository impls, parsers,
        │  (Postgres, Redis, Elasticsearch, Ollama, etc.)  │    LLM provider, search client
        └───────────────────────────────────────────────┘
```

**Dependency rule:** inner layers define interfaces; outer layers implement them. The Application layer depends on Domain interfaces; Infrastructure implements those interfaces; the API layer depends on Application. Concrete implementations are bound in the **DI container** at startup.

## 2. Logical components

```
┌──────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js 14)                          │
│  Dashboard · Alerts · Investigations · Hunts · MITRE Matrix ·          │
│  Attack Timeline · Detection Studio · Chat · Admin · Settings          │
└──────────────────────────────┬─────────────────────────────────────────┘
                   REST (JSON)  │  WebSocket (chat/stream, live alerts)
┌──────────────────────────────▼─────────────────────────────────────────┐
│                       API GATEWAY  (FastAPI)                           │
│  CORS · AuthN (JWT/OIDC) · AuthZ (RBAC) · Rate limit · Audit ·         │
│  Request-ID · Error envelope · OpenAPI · Prometheus /metrics           │
└───────┬───────────────────────────────────────────────────┬─────────────┘
        │ Application use-cases                               │
┌───────▼──────────────┐  ┌──────────────────────┐  ┌────────▼────────────┐
│   Ingestion service   │  │  Detection service    │  │  Investigation svc  │
│  parse → normalize →  │  │  rules + AI scoring → │  │  orchestrates       │
│  store (PG + ES)      │  │  alerts               │  │  agent runs + chat  │
└───────┬──────────────┘  └──────────┬───────────┘  └────────┬────────────┘
        │                            │                        │
        │                  ┌─────────▼────────────────────────▼─────────┐
        │                  │      LangGraph Multi-Agent Engine            │
        │                  │  (8 agents, shared memory, tool use)         │
        │                  └─────────┬────────────────────────────────────┘
        │                            │ LLM port
┌───────▼─────┐ ┌──────────┐ ┌───────▼──────┐ ┌──────────────┐ ┌──────────┐
│ PostgreSQL  │ │  Redis    │ │ Elasticsearch │ │   Ollama     │ │ Object   │
│ system of   │ │ cache,    │ │ event/log     │ │ local LLM +  │ │ store    │
│ record      │ │ bus, mem  │ │ search        │ │ embeddings   │ │ (files)  │
└─────────────┘ └──────────┘ └──────────────┘ └──────────────┘ └──────────┘
```

## 3. Technology choices & rationale

| Concern | Choice | Why |
|---|---|---|
| API framework | **FastAPI** | Async, Pydantic v2 validation, auto OpenAPI, great DX |
| ORM / migrations | **SQLAlchemy 2 (async) + Alembic** | Mature, async, versioned schema |
| System of record | **PostgreSQL** | Relational integrity for users, alerts, incidents, audit |
| Cache / bus / agent memory | **Redis** | Fast cache, pub/sub for live updates, shared agent state |
| Event & log search | **Elasticsearch** | Full-text + structured search over high-volume telemetry |
| AI inference | **Ollama** | **Free, local**, no API cost; pluggable provider interface |
| Agent orchestration | **LangGraph** | Graph-based multi-agent flows, state, conditional routing |
| Frontend | **Next.js 14 + TS** | App Router, RSC, SSR/streaming, strong ecosystem |
| UI kit | **Tailwind + shadcn/ui** | Accessible primitives, full design control |
| Animation | **Framer Motion** | Production-grade declarative animation |
| Charts | **Recharts** + custom D3 where needed | Composable, themeable |
| Data fetching | **TanStack Query** | Caching, mutations, websocket-friendly |
| Observability | **Prometheus + Grafana + OpenTelemetry** | Open-source standard stack |

## 4. The multi-agent engine (LangGraph)

The engine is a **stateful graph** of specialized agents that share a common `HuntState` (persisted to Redis so a hunt can resume and so agents can read each other's outputs). An **Orchestrator** node routes work based on the investigation type and intermediate findings.

```
                         ┌──────────────────┐
        user query /     │   Orchestrator    │  decides which agents to invoke,
        alert / hunt  ─▶ │  (router node)    │  in what order, and when to stop
                         └─────────┬────────┘
            ┌──────────────┬───────┼────────┬──────────────┐
            ▼              ▼       ▼        ▼              ▼
   ┌────────────────┐ ┌─────────┐ ┌───────────┐ ┌──────────────┐
   │ Threat Intel    │ │  IOC     │ │   Log      │ │   Malware    │
   │ Agent           │ │ Correl.  │ │ Investig.  │ │  Analysis    │
   └────────────────┘ └─────────┘ └───────────┘ └──────────────┘
            ▼              ▼       ▼        ▼
   ┌────────────────┐ ┌─────────┐ ┌───────────┐
   │ MITRE ATT&CK    │ │  Risk    │ │ Detection  │
   │ Mapping Agent   │ │ Scoring  │ │ Engineering│
   └────────────────┘ └─────────┘ └───────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  Reporting    │  synthesizes findings into the
                  │   Agent       │  incident report + recommendations
                  └──────────────┘
```

### Agent responsibilities

| # | Agent | Input | Output | Tools / ports |
|---|---|---|---|---|
| 1 | **Threat Intelligence** | IOCs (IPs, hashes, domains) | Reputation, known-threat context, TTP hints | TI lookup port (local enrichment DB), vector recall |
| 2 | **IOC Correlation** | Events, alerts | Clusters of related indicators across sources | ES search, graph correlation |
| 3 | **Log Investigation** | Host/user/time scope | Relevant event sequences, anomalies | ES queries, normalized-event store |
| 4 | **Malware Analysis** | File metadata, process trees, command lines | Behavioral verdict, LotL detection | YARA matching, heuristic rules |
| 5 | **MITRE ATT&CK Mapping** | Observed behaviors | Tactics/techniques (TIDs) with rationale | Local ATT&CK knowledge base |
| 6 | **Risk Scoring** | All findings | Unified confidence + severity score | Scoring model (deterministic + LLM judgment) |
| 7 | **Reporting** | All findings | Incident report, timeline, remediation | Templating, LLM summarization |
| 8 | **Detection Engineering** | Confirmed behavior | Sigma/YARA/Suricata/SPL/KQL artifacts | Rule generators |

### Shared memory & collaboration

- **Working memory** — the `HuntState` object (findings, evidence refs, scratchpad) lives in Redis, keyed by `hunt_id`. Every agent reads/appends.
- **Long-term memory** — embeddings of past incidents/findings stored in Elasticsearch (vectors via `nomic-embed-text` on Ollama) enable "have we seen this before?" recall.
- **Determinism guardrails** — agents must attach `evidence_refs` to every claim; the Risk Scoring and Reporting agents reject unsupported assertions. This keeps outputs explainable and auditable.

### Resilience

If Ollama is unreachable, the engine degrades to **rule-based-only** detection and surfaces a clear "AI features unavailable" state rather than failing requests.

## 5. Key data flows

### 5.1 Ingestion
```
upload/connector → format detection → LogParser (per source) →
normalize to common Event schema → persist (Postgres metadata + Elasticsearch body) →
emit "events.ingested" on Redis bus → Detection service consumes
```

### 5.2 Detection → alert
```
new events → rule engine (deterministic) ⨄ AI scoring (agents) →
candidate findings → dedup/correlate → Alert created (severity, confidence, evidence, MITRE) →
WebSocket push to live dashboard
```

### 5.3 AI chat investigation
```
analyst question (WS) → Orchestrator → relevant agents gather evidence →
Reporting agent streams answer tokens back over WebSocket, with evidence citations
```

## 6. Cross-cutting concerns

- **Configuration** — single `Settings` (Pydantic Settings) sourced from env; no hardcoded secrets.
- **Logging** — structured (JSON in prod) with request-ID correlation; never logs secrets/PII payloads.
- **Errors** — uniform error envelope (`{error: {code, message, details, request_id}}`); domain exceptions mapped to HTTP at the edge.
- **Idempotency** — ingestion uses content hashes to avoid duplicate event storage.
- **Background work** — long-running hunts/ingestion run as async tasks (workers), not in the request path.

## 7. Deployment topology

- **Local/dev:** Docker Compose — `backend`, `frontend`, `postgres`, `redis`, `elasticsearch`, `ollama` (optional), plus `prometheus`/`grafana` profile.
- **Production:** Kubernetes — stateless `backend` Deployment (HPA), `frontend` Deployment, worker Deployment, managed/StatefulSet Postgres + Redis + Elasticsearch, Ollama as a GPU/CPU node pool DaemonSet/Deployment. Ingress with TLS termination.

See [`11-deployment-guide.md`](11-deployment-guide.md).

## 8. Scalability & performance notes

- API is **stateless** → scale horizontally behind a load balancer.
- Heavy work (ingestion, hunts, LLM) is **async / off-request**.
- Elasticsearch handles search-heavy read load; Postgres stays lean (metadata + relational state).
- Redis fronts hot reads and carries the live-update pub/sub and agent memory.

## 9. Architecture decision records (ADRs)

Significant decisions are captured as ADRs in [`docs/adr/`](adr/). Examples: "Why Clean Architecture", "Why Ollama over hosted LLMs", "Postgres + Elasticsearch split of responsibilities".
