# ThreatMind AI — Test Plan

**Goal:** ≥ 80% coverage on backend domain + application layers, with layered tests that map to the architecture.

---

## 1. Test pyramid

```
        ╱ E2E ╲              few — full-stack user flows
      ╱─────────╲
    ╱ Integration ╲          some — API + real Postgres/Redis/ES
  ╱─────────────────╲
╱       Unit          ╲      many — pure domain/application logic
```

## 2. Test types & scope

| Type | Location | What it covers | Infra needed |
|---|---|---|---|
| **Unit** | `backend/tests/unit` | Value objects, entities, RBAC, security primitives, parsers, detection engine, agents (fake LLM), detection generators, timeline reconstruction, normalized events | None |
| **Integration** | `backend/tests/integration` | API via in-process ASGI client; repositories against a test Postgres; ES queries | Postgres/Redis (CI services) |
| **Security** | `backend/tests/security` | Token tampering/forgery, token-type confusion, RBAC bypass / privilege escalation, password salting, encryption | None |
| **E2E** | `backend/tests/e2e` | Login → ingest → detect → alert → investigate flow | Full stack |
| **Performance** | `backend/tests/performance` | Ingestion throughput, API latency targets | Full stack + load tool |
| **Frontend** | `frontend` | `tsc --noEmit`, ESLint, component build | Node |

## 3. Coverage policy

- Enforced in CI: `pytest --cov=app --cov-fail-under=80`.
- `app/main.py`, scripts, and migrations are excluded (wiring/IO).
- New business logic must ship with unit tests; coverage must not regress.

## 4. Key test cases (implemented)

**Domain & application**
- ConfidenceScore bounds + label buckets; MitreTechnique id validation.
- Alert lifecycle: assign/close invariants; AI-evidence guarantee.
- RBAC matrix: super-admin = all; read-only cannot write; analyst cannot manage users; deny-by-default.
- Security: password hash round-trip + unique salt; JWT claims; token-type confusion rejected; field encryption round-trip; TOTP verify; API-key hashing.

**Ingestion & detection**
- Sysmon parser: JSONL/array, process/network/file mapping, hash parsing, error capture.
- CloudTrail parser: Records envelope, identity extraction, mutating-tag.
- Detection engine: encoded PowerShell, Office→script (high), IAM priv-esc (critical), benign → no alerts; every alert carries evidence.

**Agents**
- Full 8-agent hunt completes with a down LLM (heuristic fallback); produces findings, risk score, markdown report.
- Threat-intel flags known-bad indicators; detection generated during hunt.
- Evidence guarantee downgrades unsupported claims.

**Detection generators**
- All five formats produce non-empty, format-correct output; unknown format raises.

**Timeline**
- Alerts reordered along the kill chain (initial_access < credential_access < impact).

**Security suite**
- Access token rejected as refresh; tampered/forged tokens rejected; refresh-hash irreversible; RBAC escalation blocked.

**Integration**
- Liveness + root respond; protected route returns 401 `UNAUTHENTICATED`.

## 5. Running

```bash
cd backend
pytest                                   # all
pytest -m unit                           # fast, no infra
pytest -m "integration or security"      # with services up
pytest --cov=app --cov-report=html       # coverage report → htmlcov/
```

> The suite targets **Python 3.11+** (the project uses `StrEnum`, `datetime.UTC`, modern typing). On the build/CI image (3.12) the full suite runs; the logic has additionally been validated against sample telemetry.

## 6. CI gates (`.github/workflows/ci.yml`)

ruff (lint+format) → mypy (types) → bandit (SAST) → pytest with coverage gate. Frontend: eslint + `next build`. PRs must pass all gates.

## 7. Roadmap for deeper testing

- Property-based tests (Hypothesis) for parsers.
- Contract tests for the LLM port against a live Ollama in a nightly job.
- k6/Locust performance scenarios wired into a scheduled workflow.
- Playwright E2E across the premium UI.
