# ThreatMind AI — Security Model

A security product must hold itself to a higher standard than the systems it monitors. This document defines authentication, authorization, data protection, and the platform threat model.

---

## 1. Authentication (AuthN)

### Local credentials
- Passwords hashed with **Argon2id** (fallback bcrypt), never stored or logged in plaintext.
- Password policy enforced server-side (length ≥ 12, complexity, breached-password rejection via local k-anonymity list).

### JWT sessions
- **Access token** — short-lived (default 30 min), `HS256` (or `RS256` in prod with key rotation), claims: `sub`, `roles`, `permissions`, `jti`, `exp`, `iat`.
- **Refresh token** — opaque, stored **hashed** in `refresh_tokens`, rotated on every use; reuse of a rotated token revokes the whole token family (theft detection).
- Logout revokes the refresh token; access tokens expire naturally (short TTL keeps the window small).

### SSO (OAuth2 / OIDC)
- Standard Authorization Code + PKCE flow against an OIDC provider (e.g. Keycloak — free/open-source — or any OIDC IdP).
- Users provisioned/just-in-time on first SSO login; role mapping from IdP claims is configurable.

### MFA (TOTP)
- RFC 6238 TOTP; secret generated server-side, shown once as QR + text for enrollment, stored **Fernet-encrypted**.
- One-time recovery codes (hashed) for device loss.
- MFA enforceable per-role (e.g. mandatory for `super_admin`, `soc_manager`).

---

## 2. Authorization (AuthZ) — RBAC

Four roles, permission-based checks (roles map to permission sets; code checks **permissions**, not role names, so the model is extensible).

### Permission keys (illustrative)
`dashboard:read`, `alerts:read`, `alerts:write`, `incidents:read`, `incidents:write`, `hunts:run`, `investigations:run`, `detections:read`, `detections:write`, `datasources:read`, `datasources:write`, `users:manage`, `roles:manage`, `audit:read`, `settings:manage`.

### Role → permission matrix
| Permission | Super Admin | SOC Manager | Analyst | Read-Only |
|---|:--:|:--:|:--:|:--:|
| dashboard:read | ✅ | ✅ | ✅ | ✅ |
| alerts:read / incidents:read / detections:read | ✅ | ✅ | ✅ | ✅ |
| alerts:write / incidents:write | ✅ | ✅ | ✅ | ❌ |
| hunts:run / investigations:run | ✅ | ✅ | ✅ | ❌ |
| detections:write | ✅ | ✅ | ✅ | ❌ |
| datasources:read | ✅ | ✅ | ✅ | ❌ |
| datasources:write | ✅ | ✅ | ❌ | ❌ |
| audit:read | ✅ | ✅ | ❌ | ❌ |
| users:manage / roles:manage | ✅ | ❌ | ❌ | ❌ |
| settings:manage | ✅ | ❌ | ❌ | ❌ |

### Enforcement
- A FastAPI dependency `require(*permissions)` guards each route; checks are also re-applied in use cases for defense in depth.
- Object-level checks where ownership matters (e.g. an analyst editing only alerts they're assigned, when policy requires).
- **Deny by default**: missing permission → `403 FORBIDDEN`.

---

## 3. Data protection

### In transit
- TLS everywhere in production (terminated at ingress/load balancer). HSTS enabled. Internal service-to-service traffic over the cluster network; mTLS optional via service mesh.

### At rest
- **Sensitive fields** (TOTP secrets, connector credentials, API keys) encrypted with **Fernet** (AES-128-CBC + HMAC) using `ENCRYPTION_KEY`; key sourced from env/secret manager, never committed.
- Database and Elasticsearch volumes encrypted at the storage layer (cloud-managed disk encryption or LUKS).
- Secrets in K8s via `Secret` objects (or external secret store); never in images or git.

### Secret handling
- All config via environment / secret manager (`Settings`). `.env` is git-ignored; only `.env.example` (no real values) is committed.
- Tokens, passwords, and raw event payloads are **never** written to logs.

---

## 4. Application security controls

| Control | Implementation |
|---|---|
| Input validation | Pydantic v2 schemas on every request; reject unknown fields |
| SQL injection | Parameterized queries via SQLAlchemy; no string-built SQL |
| Search injection | Structured ES query builders; no raw user-concatenated DSL |
| XSS | React auto-escaping; CSP header; sanitize any rendered HTML |
| CSRF | Token-based auth (no ambient cookies for the API) mitigates; SameSite for any cookie use |
| Rate limiting | Per-client sliding-window limiter (Redis-backed) on auth + expensive endpoints |
| Brute force | Login attempt throttling + temporary lockout + audit alerts |
| CORS | Explicit allow-list from `BACKEND_CORS_ORIGINS` |
| Security headers | HSTS, X-Content-Type-Options, X-Frame-Options/CSP frame-ancestors, Referrer-Policy |
| Dependency security | `pip-audit` / `npm audit` + Dependabot in CI |
| Prompt-injection (AI) | Agent inputs are scoped & sanitized; agents must cite evidence refs and cannot execute response actions in v1 |

---

## 5. Audit logging

- Every security-relevant action (auth, RBAC changes, data-source changes, alert/incident state changes, settings, exports) writes an immutable `audit_logs` row.
- Records actor, action, resource, status, IP, user-agent, request-ID, and a before/after diff in `metadata`.
- **Append-only**: no update/delete paths in the application; DB role for the app lacks UPDATE/DELETE on the table in production.
- Queryable by SOC Manager / Super Admin via `/audit`.

---

## 6. Platform threat model (STRIDE summary)

| Threat | Example | Mitigation |
|---|---|---|
| **S**poofing | Stolen token replay | Short TTLs, refresh rotation + reuse detection, MFA |
| **T**ampering | Altering an alert/audit record | RBAC writes, append-only audit, integrity via DB constraints |
| **R**epudiation | "I didn't close that incident" | Comprehensive audit log with actor + request-ID |
| **I**nformation disclosure | Leaking event PII | Least-privilege RBAC, encryption, no secrets in logs, read-only role |
| **D**enial of service | Flooding ingest/LLM | Rate limiting, async off-request processing, resource quotas |
| **E**levation of privilege | Analyst → admin | Deny-by-default permission checks at API **and** use-case layers |

Additional AI-specific risks:
- **Prompt injection via ingested logs** → agents treat ingested content as untrusted data, never as instructions; outputs are constrained to evidence-cited findings.
- **Hallucinated findings** → Risk Scoring + Reporting agents reject claims without `evidence_refs`; confidence scores surfaced to analysts; human-in-the-loop for response.

---

## 7. Secure SDLC

- Secrets scanning, `pip-audit`/`npm audit`, SAST (Bandit/Semgrep), and dependency review run in CI on every PR.
- A dedicated security test suite (`tests/security/`) covers authn/authz bypass, rate limiting, and injection.
- Least-privilege DB roles; principle applied to service accounts and K8s RBAC.
- See [`11-deployment-guide.md`](11-deployment-guide.md) for production hardening checklist.
