<div align="center">

# 🛡️ ThreatMind AI

### Enterprise AI-Powered Threat Hunting & Security Operations Platform

*Autonomous threat hunting, alert triage, and incident response powered by a multi-agent AI system — running entirely on free, local, open-source infrastructure.*

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-000000.svg)](https://ollama.com)

</div>

---

## Overview

**ThreatMind AI** is an enterprise-grade Security Operations Center (SOC) platform that automates the work analysts do by hand today — investigating alerts, correlating logs, looking up threat intelligence, mapping activity to MITRE ATT&CK, and writing incident reports.

It is built around a **multi-agent AI architecture** (LangGraph) where specialized agents collaborate to hunt threats autonomously across endpoints, cloud workloads, identities, and network devices.

> 💡 **100% free & local.** ThreatMind AI uses [Ollama](https://ollama.com) for all AI inference. There are **no paid APIs, no cloud billing, and no payment integrations** anywhere in this project. Runs on macOS, Windows, and Linux.

## Key Capabilities

| Capability | Description |
|---|---|
| 🤖 **Multi-Agent Threat Hunting** | 8 specialized LangGraph agents that collaborate and share memory |
| 📥 **Universal Ingestion** | Sysmon, Windows Event Logs, Linux auditd, CrowdStrike, Sentinel, Splunk, Elastic, Zeek, Suricata, firewall/DNS/proxy logs, CloudTrail, Azure & GCP audit logs |
| 🎯 **AI Detection** | Ransomware, credential dumping, privilege escalation, persistence, lateral movement, LotL, exfiltration, C2, insider & cloud threats — with confidence scores + evidence |
| 🧬 **Attack Timeline Reconstruction** | Visual attack chains mapped to the MITRE ATT&CK kill chain |
| 💬 **AI Chat Investigation** | Ask natural-language questions; get analyst-quality answers with cited evidence |
| ⚙️ **Detection Engineering** | Auto-generate Sigma, YARA, Suricata rules, Splunk SPL & KQL queries |
| 🔐 **Enterprise Security** | JWT, OAuth/SSO, MFA, RBAC (4 roles), audit logging, rate limiting, encryption |
| 📊 **Premium SOC UI** | Dark/light, fully responsive, interactive charts, threat heatmaps, MITRE matrix |

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js + shadcn/ui)                 │
│   Dashboard · Investigations · MITRE Matrix · Timeline · Chat     │
└───────────────────────────────┬───────────────────────────────────┘
                                 │ REST / WebSocket
┌───────────────────────────────▼───────────────────────────────────┐
│                      API Gateway (FastAPI)                         │
│         Auth · RBAC · Rate Limiting · Audit · OpenAPI              │
├───────────────────────────────────────────────────────────────────┤
│  Application Layer  (use cases, orchestration, DI)                 │
├───────────────────────────────────────────────────────────────────┤
│  Domain Layer       (entities, value objects, business rules)      │
├───────────────────────────────────────────────────────────────────┤
│  Infrastructure     (repositories, parsers, LLM, search)           │
└───────┬───────────────┬───────────────┬───────────────┬───────────┘
        │               │               │               │
   ┌────▼────┐    ┌─────▼─────┐   ┌─────▼──────┐   ┌────▼─────┐
   │Postgres │    │   Redis   │   │Elasticsearch│   │  Ollama  │
   │ (state) │    │(cache/bus)│   │ (log search)│   │  (LLM)   │
   └─────────┘    └───────────┘   └────────────┘   └──────────┘
                                          ▲
                          ┌───────────────┴────────────────┐
                          │   LangGraph Multi-Agent Engine   │
                          │  ThreatIntel · IOC · LogInvest ·  │
                          │  Malware · MITRE · RiskScore ·    │
                          │  Reporting · DetectionEng         │
                          └──────────────────────────────────┘
```

See [`docs/02-system-architecture.md`](docs/02-system-architecture.md) for the full design.

## Tech Stack

**Backend** — Python 3.11+ · FastAPI · SQLAlchemy 2 · Alembic · Pydantic v2 · LangGraph · PostgreSQL · Redis · Elasticsearch
**Frontend** — Next.js 14 (App Router) · TypeScript · TailwindCSS · shadcn/ui · Framer Motion · Recharts · TanStack Query
**AI** — Ollama (local LLMs: `llama3.1`, `qwen2.5`, etc.) behind a pluggable provider interface
**Infra** — Docker · Docker Compose · Kubernetes · GitHub Actions · Prometheus · Grafana · OpenTelemetry

## Quick Start

> Prerequisites: [Docker Desktop](https://www.docker.com/products/docker-desktop/), and [Ollama](https://ollama.com/download) (or run Ollama via Compose).

```bash
# 1. Clone & configure
git clone <repo-url> threatmind-ai && cd threatmind-ai
cp .env.example .env            # macOS / Linux
# copy .env.example .env        # Windows (PowerShell: Copy-Item .env.example .env)

# 2. Pull a local model
ollama pull llama3.1

# 3. Launch the full stack
docker compose up -d

# 4. Open the app
#    Frontend  → http://localhost:3000
#    API docs  → http://localhost:8000/docs
```

Detailed setup, including running backend/frontend natively for development, lives in [`docs/11-deployment-guide.md`](docs/11-deployment-guide.md).

## Documentation

| Doc | Contents |
|---|---|
| [01 – PRD](docs/01-prd.md) | Product requirements, personas, user stories |
| [02 – System Architecture](docs/02-system-architecture.md) | Components, data flow, agent design |
| [03 – Database Schema](docs/03-database-schema.md) | ERD, tables, relationships |
| [04 – API Design](docs/04-api-design.md) | Endpoints, contracts, error model |
| [05 – Folder Structure](docs/05-folder-structure.md) | Monorepo layout & conventions |
| [06 – Security Model](docs/06-security-model.md) | AuthN/Z, RBAC, threat model |
| [11 – Deployment Guide](docs/11-deployment-guide.md) | Local, Docker, K8s, CI/CD |

## Project Status

All six delivery phases are in place (foundation → frontend → ingestion/detection
→ multi-agent engine → AI chat → detection-engineering/MITRE/timeline →
hardening/infra). See [`docs/00-roadmap.md`](docs/00-roadmap.md) for the phase
plan and [`docs/12-deliverables-map.md`](docs/12-deliverables-map.md) for a map of
every deliverable to its location in the repo.

Built in vertical slices: it is a coherent, runnable, architecturally-correct
platform that spans every requested area. Two data-source parsers are fully
implemented (Sysmon, CloudTrail); the remaining declared sources follow the same
`LogParser` interface. AI features run on local Ollama and degrade gracefully to
deterministic heuristics when it is unavailable.

> **Requires Python 3.11+** for the backend (uses `StrEnum`, `datetime.UTC`).
> Use Docker (recommended) or install 3.11+ natively.

## License

Apache 2.0 — see [LICENSE](LICENSE). Built with free and open-source software only.
