# ThreatMind AI — Deployment Guide

Covers local development, the Docker Compose stack, and Kubernetes — on **macOS, Windows, and Linux**. Everything here uses free/open-source software.

---

## 1. Prerequisites

| Tool | Local (native) dev | Docker stack |
|---|---|---|
| Git | ✅ | ✅ |
| Docker Desktop (Compose v2) | optional | ✅ required |
| Python 3.11+ | ✅ | — (in container) |
| Node.js 20+ | ✅ | — (in container) |
| Ollama | ✅ (or via Compose) | optional service |

> **Why Python 3.11+:** the backend uses modern typing and async features. macOS ships 3.9 — install 3.11+ via [python.org](https://www.python.org/downloads/), Homebrew (`brew install python@3.12`), or pyenv. On Windows use the python.org installer or `winget install Python.Python.3.12`.

---

## 2. Quick start (Docker Compose — recommended)

```bash
# macOS / Linux
cp .env.example .env
make setup          # builds images
make up             # starts the stack

# Windows (PowerShell)
Copy-Item .env.example .env
./scripts/dev.ps1 setup
./scripts/dev.ps1 up
```

Pull a model for the AI features (host Ollama):
```bash
ollama pull llama3.1
ollama pull nomic-embed-text   # embeddings for agent memory
```

Then open:
- Frontend → http://localhost:3000
- API docs → http://localhost:8000/docs
- Grafana (with `--profile observability`) → http://localhost:3001

Apply DB migrations & seed initial data:
```bash
make db-migrate && make db-seed         # macOS/Linux
./scripts/dev.ps1 db-migrate; ./scripts/dev.ps1 db-seed   # Windows
```

---

## 3. Native development (without containers for app code)

Run infra (Postgres/Redis/ES) in Docker, app code on the host for fast reloads.

```bash
docker compose up -d postgres redis elasticsearch   # infra only

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

---

## 4. Configuration

All configuration is environment-driven (see `.env.example`). Inside the Docker network, hostnames are service names (`postgres`, `redis`, `elasticsearch`, `ollama`); for native dev they are `localhost`. Generate strong secrets before any non-local use:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"            # SECRET_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # ENCRYPTION_KEY
```

---

## 5. Kubernetes (production)

Manifests/kustomize live in `infra/k8s/` with `base/` and per-environment `overlays/`.

```bash
kubectl apply -k infra/k8s/overlays/prod
```

Production components:
- `backend` Deployment + HPA (stateless), `frontend` Deployment, `worker` Deployment (ingestion/hunts).
- StatefulSets (or managed services) for Postgres, Redis, Elasticsearch.
- Ollama Deployment (CPU or GPU node pool).
- Ingress with TLS (cert-manager + Let's Encrypt — free).
- Secrets via K8s `Secret` / external secret store; never baked into images.

### Cloud portability (AWS / Azure / GCP)
The stack is cloud-agnostic (plain Kubernetes + containers). Map managed services as desired:
| Component | AWS | Azure | GCP |
|---|---|---|---|
| Kubernetes | EKS | AKS | GKE |
| Postgres | RDS | Azure DB for PostgreSQL | Cloud SQL |
| Redis | ElastiCache | Azure Cache for Redis | Memorystore |
| Search | OpenSearch | Elastic on Azure | Elastic on GKE |
| Object store | S3 | Blob Storage | GCS |

(Using managed services is optional and may incur cloud cost — the self-hosted in-cluster option remains fully free.)

---

## 6. CI/CD (GitHub Actions)

Pipelines in `.github/workflows/`:
- **ci.yml** — lint (ruff/eslint), type-check (mypy/tsc), unit+integration tests with coverage gate (≥80%), security scans (bandit/semgrep, pip-audit/npm audit), build images.
- **cd.yml** — on tag/main: build & push images, run migrations, deploy via kustomize to the target environment.

---

## 7. Observability

- Enable the observability profile: `docker compose --profile observability up -d`.
- Prometheus scrapes `/metrics`; Grafana ships with dashboards for API latency, AI/agent usage, DB, and ingestion throughput.
- OpenTelemetry traces exported to the OTLP endpoint when `OTEL_ENABLED=true`.

---

## 8. Production hardening checklist

- [ ] Strong, rotated `SECRET_KEY` and `ENCRYPTION_KEY` from a secret manager.
- [ ] `ENVIRONMENT=production`, `DEBUG=false`, `LOG_JSON=true`.
- [ ] TLS at ingress; HSTS + security headers verified.
- [ ] DB app-role lacks UPDATE/DELETE on `audit_logs`.
- [ ] Rate limits tuned; brute-force lockout enabled.
- [ ] MFA enforced for privileged roles.
- [ ] Backups for Postgres + Elasticsearch; restore tested.
- [ ] Resource limits/quotas set; HPA configured.
- [ ] Dependency & image scans clean.
- [ ] Audit log shipping to durable storage.
```
