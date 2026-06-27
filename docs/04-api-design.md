# ThreatMind AI — API Design

**Base URL:** `/api/v1` · **Auth:** Bearer JWT (or API key) · **Format:** JSON · **Spec:** auto-generated OpenAPI at `/docs` (Swagger) and `/redoc`.

---

## 1. Conventions

### Authentication
- `Authorization: Bearer <access_token>` for user sessions.
- `X-API-Key: <key>` for connectors/automation.
- Access tokens are short-lived (30 min); refresh via `/auth/refresh`. Refresh tokens rotate on use.

### Standard response envelope
Success responses return the resource (or a paginated list); errors always use:
```json
{
  "error": {
    "code": "ALERT_NOT_FOUND",
    "message": "Alert 3f2a… does not exist.",
    "details": {},
    "request_id": "01J..."
  }
}
```

### Pagination
List endpoints accept `?page=1&page_size=25&sort=-created_at` and return:
```json
{
  "items": [ ... ],
  "page": 1,
  "page_size": 25,
  "total": 1043,
  "total_pages": 42
}
```

### Filtering
Resource-appropriate query params, e.g. `/alerts?status=new&severity=critical&host=WIN-001&from=2026-06-01&to=2026-06-27&q=powershell`.

### Errors → HTTP status
| Code family | HTTP | Meaning |
|---|---|---|
| `*_VALIDATION` | 422 | Request body/params invalid |
| `UNAUTHENTICATED` | 401 | Missing/invalid/expired token |
| `FORBIDDEN` | 403 | Authenticated but lacks permission |
| `*_NOT_FOUND` | 404 | Resource missing |
| `CONFLICT` | 409 | State conflict (e.g. duplicate) |
| `RATE_LIMITED` | 429 | Too many requests |
| `AI_UNAVAILABLE` | 503 | Ollama/agents unavailable |
| `INTERNAL` | 500 | Unexpected |

### Rate limiting
Per-client (token/API-key/IP) sliding window. Response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`. Exceeding → 429 with `Retry-After`.

### Idempotency & request IDs
Every response carries `X-Request-ID` (also echoed in logs and the error envelope). Ingestion dedups by content hash.

---

## 2. Endpoint catalog

### 2.1 Auth & identity — `/auth`
| Method | Path | Description | Min role |
|---|---|---|---|
| POST | `/auth/login` | Email+password → access/refresh tokens (or MFA challenge) | public |
| POST | `/auth/mfa/verify` | Complete TOTP challenge → tokens | public (challenge token) |
| POST | `/auth/refresh` | Rotate refresh → new access/refresh | public (refresh token) |
| POST | `/auth/logout` | Revoke current refresh token | authenticated |
| GET  | `/auth/sso/{provider}/login` | Begin OIDC SSO flow | public |
| GET  | `/auth/sso/{provider}/callback` | OIDC callback → tokens | public |
| GET  | `/auth/me` | Current user + roles + permissions | authenticated |
| POST | `/auth/mfa/enroll` | Begin TOTP enrollment (QR/secret) | authenticated |
| POST | `/auth/mfa/enroll/confirm` | Confirm enrollment | authenticated |

### 2.2 Users & roles (admin) — `/users`, `/roles`
| Method | Path | Description | Min role |
|---|---|---|---|
| GET | `/users` | List users | super_admin |
| POST | `/users` | Create user | super_admin |
| GET | `/users/{id}` | Get user | super_admin |
| PATCH | `/users/{id}` | Update user (activate, roles…) | super_admin |
| DELETE | `/users/{id}` | Soft-delete user | super_admin |
| GET | `/roles` | List roles & permissions | super_admin |

### 2.3 Data sources & ingestion — `/data-sources`, `/ingest`
| Method | Path | Description | Min role |
|---|---|---|---|
| GET | `/data-sources` | List connectors | analyst |
| POST | `/data-sources` | Create connector | soc_manager |
| PATCH | `/data-sources/{id}` | Update/enable/disable | soc_manager |
| DELETE | `/data-sources/{id}` | Remove connector | soc_manager |
| POST | `/ingest/upload` | Upload a log file (multipart) → ingest job | analyst |
| GET | `/ingest/jobs` | List ingest jobs | analyst |
| GET | `/ingest/jobs/{id}` | Job status/progress | analyst |

### 2.4 Events (search) — `/events`
| Method | Path | Description | Min role |
|---|---|---|---|
| GET | `/events` | Search normalized events (ES-backed): `q`, `host`, `user`, `source_type`, time range | analyst |
| GET | `/events/{id}` | Single normalized event | analyst |

### 2.5 Alerts — `/alerts`
| Method | Path | Description | Min role |
|---|---|---|---|
| GET | `/alerts` | List/filter alerts | read_only |
| GET | `/alerts/{id}` | Alert detail incl. evidence, MITRE, explanation | read_only |
| PATCH | `/alerts/{id}` | Update status/assignee | analyst |
| POST | `/alerts/{id}/assign` | Assign to user | analyst |
| POST | `/alerts/{id}/close` | Close (resolved/false_positive) | analyst |
| POST | `/alerts/{id}/investigate` | Launch AI investigation for this alert | analyst |

### 2.6 Incidents — `/incidents`
| Method | Path | Description | Min role |
|---|---|---|---|
| GET | `/incidents` | List incidents | read_only |
| GET | `/incidents/{id}` | Incident detail | read_only |
| POST | `/incidents` | Create incident (group alerts) | analyst |
| PATCH | `/incidents/{id}` | Update status/assignee | analyst |
| GET | `/incidents/{id}/timeline` | Reconstructed attack timeline | read_only |
| GET | `/incidents/{id}/report` | Generated report (md) | read_only |
| POST | `/incidents/{id}/report:generate` | (Re)generate report via Reporting agent | analyst |
| GET | `/incidents/{id}/report.pdf` | Export report as PDF | read_only |

### 2.7 IOCs — `/iocs`
| Method | Path | Description | Min role |
|---|---|---|---|
| GET | `/iocs` | List/search IOCs | read_only |
| GET | `/iocs/{id}` | IOC detail + enrichment | read_only |
| POST | `/iocs/{id}/enrich` | Run Threat Intel agent enrichment | analyst |

### 2.8 Threat hunting & investigations — `/hunts`, `/investigations`
| Method | Path | Description | Min role |
|---|---|---|---|
| POST | `/hunts` | Launch autonomous hunt (scope, time range, focus) | analyst |
| GET | `/hunts/{id}` | Hunt status + findings | analyst |
| POST | `/hunts/{id}/cancel` | Cancel a running hunt | analyst |
| GET | `/investigations` | List investigations | analyst |
| GET | `/investigations/{id}` | Investigation detail incl. agent runs | analyst |
| GET | `/investigations/{id}/runs` | Per-agent run traces | analyst |

### 2.9 AI chat — `/chat` (WebSocket + REST)
| Method | Path | Description | Min role |
|---|---|---|---|
| WS | `/chat/ws` | Streaming investigation chat (tokens + evidence events) | analyst |
| POST | `/chat/sessions` | Create a chat session | analyst |
| GET | `/chat/sessions/{id}` | Session history | analyst |

WebSocket message protocol:
```jsonc
// client → server
{ "type": "user_message", "session_id": "…", "content": "Investigate host WIN-001" }
// server → client (streamed)
{ "type": "token", "content": "WIN-001 shows…" }
{ "type": "evidence", "ref": { "event_id": "…", "summary": "…" } }
{ "type": "agent_step", "agent": "log_investigation", "status": "completed" }
{ "type": "done", "investigation_id": "…" }
```

### 2.10 MITRE ATT&CK — `/mitre`
| Method | Path | Description | Min role |
|---|---|---|---|
| GET | `/mitre/matrix` | Full tactic/technique matrix + coverage overlay | read_only |
| GET | `/mitre/techniques/{id}` | Technique detail + related alerts | read_only |

### 2.11 Detection engineering — `/detections`
| Method | Path | Description | Min role |
|---|---|---|---|
| GET | `/detections` | List generated rules/queries | analyst |
| POST | `/detections:generate` | Generate from a finding/behavior (format=sigma\|yara\|suricata\|splunk_spl\|kql) | analyst |
| GET | `/detections/{id}` | Detail | analyst |
| PATCH | `/detections/{id}` | Edit / change status | analyst |
| POST | `/detections/{id}/validate` | Lint/validate syntax | analyst |

### 2.12 Dashboard & metrics — `/dashboard`
| Method | Path | Description | Min role |
|---|---|---|---|
| GET | `/dashboard/overview` | KPI cards: open alerts, MTTR/MTTI, severity breakdown | read_only |
| GET | `/dashboard/threat-heatmap` | Heatmap data (host × category, time) | read_only |
| GET | `/dashboard/trends` | Time-series of alerts/incidents | read_only |

### 2.13 Audit & admin — `/audit`, `/settings`
| Method | Path | Description | Min role |
|---|---|---|---|
| GET | `/audit` | Query audit log | soc_manager |
| GET | `/settings` | Platform settings | super_admin |
| PATCH | `/settings` | Update settings | super_admin |

### 2.14 System — `/health`, `/metrics`
| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/health/live` | Liveness probe | none |
| GET | `/health/ready` | Readiness (DB/Redis/ES/Ollama checks) | none |
| GET | `/metrics` | Prometheus metrics | internal |

---

## 3. Example exchanges

### Login (with MFA)
```http
POST /api/v1/auth/login
{ "email": "priya@corp.com", "password": "•••••" }

200 OK
{ "mfa_required": true, "challenge_token": "eyJ…" }
```
```http
POST /api/v1/auth/mfa/verify
{ "challenge_token": "eyJ…", "code": "123456" }

200 OK
{ "access_token": "eyJ…", "refresh_token": "eyJ…", "token_type": "bearer", "expires_in": 1800 }
```

### List critical new alerts
```http
GET /api/v1/alerts?status=new&severity=critical&sort=-created_at&page=1&page_size=25
Authorization: Bearer eyJ…
```

### Launch a hunt
```http
POST /api/v1/hunts
Authorization: Bearer eyJ…
{
  "focus": "ransomware",
  "scope": { "hosts": ["WIN-001","WIN-014"] },
  "time_range": { "from": "2026-06-25T00:00:00Z", "to": "2026-06-27T00:00:00Z" }
}

202 Accepted
{ "id": "hunt_01J…", "status": "running" }
```

### Generate a Sigma rule
```http
POST /api/v1/detections:generate
Authorization: Bearer eyJ…
{ "source_alert_id": "3f2a…", "format": "sigma" }

201 Created
{ "id": "det_01J…", "format": "sigma", "content": "title: Suspicious PowerShell…", "status": "draft" }
```

---

## 4. Versioning & deprecation

URL-versioned (`/api/v1`). Breaking changes ship under a new version; deprecated endpoints return `Deprecation` and `Sunset` headers for at least one minor cycle before removal.
