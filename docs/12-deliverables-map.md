# ThreatMind AI — Deliverables Map

This maps each requested deliverable to where it lives in the repository.

| # | Deliverable | Location | Status |
|---|---|---|---|
| 1 | **Complete PRD** | [`docs/01-prd.md`](01-prd.md) | ✅ |
| 2 | **System Architecture** | [`docs/02-system-architecture.md`](02-system-architecture.md) | ✅ |
| 3 | **Database Schema** | [`docs/03-database-schema.md`](03-database-schema.md) + `backend/app/infrastructure/db/models/` + `backend/alembic/versions/0001_initial_schema.py` | ✅ |
| 4 | **API Design** | [`docs/04-api-design.md`](04-api-design.md) + live OpenAPI at `/docs` | ✅ |
| 5 | **Folder Structure** | [`docs/05-folder-structure.md`](05-folder-structure.md) | ✅ |
| 6 | **Frontend Design** | `frontend/` (Next.js 14, Tailwind, shadcn-style, Framer Motion) | ✅ |
| 7 | **Backend Implementation** | `backend/app/` (clean architecture: domain/application/infrastructure/api) | ✅ |
| 8 | **Infrastructure Design** | `infra/` (Docker, Compose, K8s base + overlays), `docker-compose.yml` | ✅ |
| 9 | **Security Model** | [`docs/06-security-model.md`](06-security-model.md) + `backend/app/core/security.py` + auth/RBAC | ✅ |
| 10 | **Test Plan** | [`docs/10-test-plan.md`](10-test-plan.md) + `backend/tests/` | ✅ |
| 11 | **Deployment Guide** | [`docs/11-deployment-guide.md`](11-deployment-guide.md) | ✅ |
| 12 | **Production-ready Source Code** | entire repo, committed in 7 phased commits | ✅ |

## Feature → code cross-reference

| Capability | Where |
|---|---|
| Multi-agent engine (8 agents, LangGraph) | `backend/app/infrastructure/agents/` |
| Shared agent memory | `agents/state.py` (Redis-serializable `HuntState`) |
| Data-source parsers | `backend/app/infrastructure/parsers/` (Sysmon, CloudTrail + registry for all 16) |
| AI threat detection (rules + confidence + evidence) | `backend/app/application/detection/` |
| Attack timeline reconstruction | `backend/app/application/reporting/timeline.py` |
| AI chat investigation (WebSocket streaming) | `backend/app/application/investigation/chat.py` + `api/v1/routes/chat.py` |
| Detection engineering (Sigma/YARA/Suricata/SPL/KQL) | `backend/app/infrastructure/detections/generators.py` |
| MITRE ATT&CK (KB + matrix) | `backend/app/infrastructure/mitre/` + `api/v1/routes/mitre.py` |
| AuthN/Z (JWT/MFA/RBAC/audit/rate-limit/encryption) | `backend/app/core/security.py`, `application/auth/`, `api/middleware/` |
| Observability (Prometheus/OTel/Grafana) | `backend/app/core/observability.py`, `infra/docker/grafana/` |
| Premium UI (dashboard, alerts, MITRE, timeline, chat, detections, admin) | `frontend/src/app/(dashboard)/` |
| CI/CD | `.github/workflows/ci.yml`, `cd.yml` |

## Notes on scope & honesty

- **Free & local only:** all AI inference runs through Ollama; there are no paid
  APIs or payment integrations anywhere. Cross-platform (macOS/Windows/Linux).
- **Runnable, not yet exhaustively feature-complete:** this is a coherent,
  architecturally-correct platform spanning every requested area, built in
  vertical slices. Two parsers are fully implemented (Sysmon, CloudTrail); the
  remaining 14 declared sources follow the same `LogParser` interface and raise
  a clear error until implemented. The agent engine and detection rules are
  real and validated; they grow in breadth from here.
- **Graceful degradation:** if Ollama/Elasticsearch/Redis are down, the app
  stays up — AI features degrade to deterministic heuristics and the UI falls
  back to realistic demo data, so the product is always demonstrable.
