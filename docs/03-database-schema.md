# ThreatMind AI — Database Schema

**Store split:** PostgreSQL is the **system of record** for relational/transactional state (identity, alerts, incidents, audit). **Elasticsearch** holds the high-volume normalized **events/logs** (full bodies) for search; Postgres keeps only lightweight event *references* where a relation is needed.

All Postgres tables use UUID primary keys (`uuid_generate_v4()` / app-generated UUIDv7), `created_at` / `updated_at` timestamptz, and soft-delete (`deleted_at`) where appropriate.

---

## 1. Entity-relationship overview

```
                    ┌──────────┐        ┌──────────────┐
                    │  roles    │◀──────│ user_roles    │
                    └──────────┘        └──────┬───────┘
                                                │
                    ┌──────────┐                ▼
                    │  users    │────────▶ (M:N) ────────┐
                    └────┬─────┘                          │
                         │ 1:N                            │
        ┌────────────────┼───────────────┬───────────────┴───────┐
        ▼                ▼               ▼                        ▼
 ┌────────────┐  ┌──────────────┐ ┌──────────────┐       ┌──────────────┐
 │ audit_logs  │  │  api_keys     │ │ user_mfa      │       │ refresh_tokens│
 └────────────┘  └──────────────┘ └──────────────┘       └──────────────┘

 ┌──────────────┐   1:N   ┌──────────────┐   N:1   ┌──────────────┐
 │ data_sources  │────────▶│ ingest_jobs   │────────▶│   users       │
 └──────────────┘         └──────┬───────┘         └──────────────┘
                                  │ produces (refs in ES)
                                  ▼
 ┌──────────────┐   N:M    ┌──────────────┐   N:M   ┌──────────────┐
 │   alerts      │◀────────▶│  incidents    │◀───────▶│  iocs         │
 └──────┬───────┘  via      └──────┬───────┘         └──────────────┘
        │          incident_alerts  │ 1:N
        │ N:M                        ▼
        │              ┌──────────────────────┐
        │              │  timeline_events       │
        │              └──────────────────────┘
        ▼ via alert_techniques (N:M)
 ┌──────────────┐
 │ mitre_       │
 │ techniques    │
 └──────────────┘

 ┌──────────────┐   1:N   ┌──────────────┐
 │ investigations│────────▶│ agent_runs    │──┐ 1:N
 └──────────────┘         └──────┬───────┘  │
                                  │          ▼
                                  │   ┌──────────────┐
                                  └──▶│ agent_messages│
                                      └──────────────┘

 ┌──────────────┐
 │ detections    │  (generated Sigma/YARA/Suricata/SPL/KQL artifacts)
 └──────────────┘
```

---

## 2. Identity & access tables

### `users`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| email | citext UNIQUE NOT NULL | login identifier |
| full_name | text | |
| hashed_password | text | bcrypt/argon2; null if SSO-only |
| is_active | bool default true | |
| is_sso | bool default false | provisioned via OIDC |
| sso_subject | text | OIDC `sub`, unique when present |
| last_login_at | timestamptz | |
| created_at / updated_at / deleted_at | timestamptz | |

### `roles`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| name | text UNIQUE | `super_admin` \| `soc_manager` \| `analyst` \| `read_only` |
| description | text | |
| permissions | jsonb | denormalized permission keys for fast checks |

### `user_roles` (M:N)
`user_id` FK → users, `role_id` FK → roles, PK(user_id, role_id), `granted_by`, `granted_at`.

### `user_mfa`
`user_id` FK (1:1), `totp_secret` (Fernet-encrypted), `enabled` bool, `verified_at`, `recovery_codes` (hashed, jsonb).

### `refresh_tokens`
`id` UUID PK, `user_id` FK, `token_hash` (sha256), `expires_at`, `revoked_at`, `user_agent`, `ip`. Enables rotation & revocation.

### `api_keys`
`id` UUID PK, `user_id` FK, `name`, `prefix` (visible), `key_hash`, `scopes` jsonb, `last_used_at`, `expires_at`, `revoked_at`. For connector/automation access.

### `audit_logs`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| actor_id | UUID FK users (nullable for system) | |
| actor_label | text | email/snapshot at event time |
| action | text | e.g. `alert.close`, `user.create`, `auth.login` |
| resource_type | text | |
| resource_id | text | |
| status | text | `success` \| `failure` |
| ip / user_agent | text | |
| metadata | jsonb | before/after diff, request_id |
| created_at | timestamptz | indexed; append-only (no updates/deletes) |

---

## 3. Ingestion tables

### `data_sources`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| name | text | "Prod Sysmon", "AWS CloudTrail – acct 1234" |
| source_type | enum | sysmon, windows_event, linux_auditd, crowdstrike, sentinel, splunk, elastic, zeek, suricata, edr, firewall, dns, proxy, cloudtrail, azure_activity, gcp_audit |
| config | jsonb | connector settings (no secrets in plaintext — encrypted) |
| enabled | bool | |
| created_by | UUID FK users | |
| created_at / updated_at | | |

### `ingest_jobs`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| data_source_id | UUID FK | |
| status | enum | queued, running, completed, failed |
| file_name / file_hash | text | dedup via hash |
| events_total / events_ingested / events_failed | int | |
| error | text | |
| started_at / finished_at | timestamptz | |

> **Normalized events** themselves live in Elasticsearch (`{prefix}-events-*`), not Postgres. See §7.

---

## 4. Detection & incident tables

### `alerts`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| title | text | |
| description | text | |
| category | enum | ransomware, credential_dumping, privilege_escalation, persistence, lateral_movement, lotl, exfiltration, c2, insider, cloud_attack, other |
| severity | enum | critical, high, medium, low, info |
| confidence | smallint | 0–100 |
| status | enum | new, triaging, investigating, resolved, false_positive, suppressed |
| source | enum | rule, ai, hybrid |
| host | text | affected host (denormalized for filtering) |
| user_principal | text | affected identity |
| evidence | jsonb | array of `{event_id (ES), summary, fields}` |
| explanation | text | analyst-readable rationale |
| assigned_to | UUID FK users | nullable |
| first_seen / last_seen | timestamptz | |
| created_at / updated_at | | |

Indexes: `(status, severity)`, `(category)`, `(host)`, `(created_at desc)`, GIN on `evidence`.

### `incidents`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| title | text | |
| summary | text | AI/analyst summary |
| severity | enum | rolled up from alerts |
| status | enum | open, investigating, contained, closed |
| risk_score | smallint | 0–100 |
| assigned_to | UUID FK users | |
| report_markdown | text | generated incident report |
| opened_at / closed_at | timestamptz | |

### `incident_alerts` (M:N)
`incident_id` FK, `alert_id` FK, PK(incident_id, alert_id).

### `iocs`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| type | enum | ip, domain, url, file_hash, email, registry_key, process, mutex |
| value | text | |
| reputation | enum | malicious, suspicious, benign, unknown |
| first_seen / last_seen | timestamptz | |
| enrichment | jsonb | TI agent output |
UNIQUE(type, value). Linked to alerts/incidents via `alert_iocs` / `incident_iocs` (M:N).

### `mitre_techniques`
Seed/reference table mirroring the local ATT&CK knowledge base.
`id` (e.g. `T1059.001`) PK text, `name`, `tactic` enum, `description`, `url`.

### `alert_techniques` (M:N)
`alert_id` FK, `technique_id` FK → mitre_techniques, `confidence` smallint, `rationale` text.

### `timeline_events`
Reconstructed attack-chain steps for an incident.
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| incident_id | UUID FK | |
| phase | enum | initial_access, execution, persistence, priv_esc, defense_evasion, cred_access, discovery, lateral_movement, collection, c2, exfiltration, impact |
| occurred_at | timestamptz | |
| title / description | text | |
| technique_id | text FK mitre_techniques | nullable |
| evidence_refs | jsonb | ES event ids |
| order_index | int | display ordering |

---

## 5. AI / investigation tables

### `investigations`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| type | enum | chat, autonomous_hunt, alert_triage |
| title | text | |
| query | text | initiating prompt / scope |
| status | enum | running, completed, failed, cancelled |
| created_by | UUID FK users | |
| incident_id | UUID FK | nullable link |
| summary | text | final synthesized result |
| created_at / completed_at | | |

### `agent_runs`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| investigation_id | UUID FK | |
| agent | enum | threat_intel, ioc_correlation, log_investigation, malware_analysis, mitre_mapping, risk_scoring, reporting, detection_engineering, orchestrator |
| status | enum | running, completed, failed |
| input | jsonb | |
| output | jsonb | findings + evidence_refs |
| tokens / latency_ms | int | observability |
| started_at / finished_at | | |

### `agent_messages`
Conversation/scratchpad trace (for replay & audit).
`id` PK, `agent_run_id` FK, `role` (system/user/assistant/tool), `content` text, `tool_name` text nullable, `created_at`.

---

## 6. Detection engineering table

### `detections`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| name | text | |
| format | enum | sigma, yara, suricata, splunk_spl, kql |
| content | text | the rule/query body |
| language_meta | jsonb | parsed metadata (logsource, level…) |
| source_alert_id | UUID FK alerts | nullable origin |
| mitre_techniques | jsonb | |
| status | enum | draft, validated, deployed, archived |
| created_by | UUID FK users | |
| created_at / updated_at | | |

---

## 7. Elasticsearch indices

| Index pattern | Contents |
|---|---|
| `{prefix}-events-*` | Normalized events (ECS-inspired): `@timestamp`, `source_type`, `host`, `user`, `process`, `network`, `file`, `cloud`, `raw`, `ingest_job_id`, `event_hash` |
| `{prefix}-memory` | Vector embeddings of past findings/incidents for long-term agent recall (`vector` dense_vector, `text`, `ref_type`, `ref_id`) |

Normalized event schema is defined in code as `domain/events/normalized_event.py` and documented in [`05-folder-structure.md`](05-folder-structure.md).

---

## 8. Migrations & seeding

- Schema managed by **Alembic** (`backend/alembic/versions`).
- Seed script (`app.scripts.seed`) inserts the four roles with permission sets, the MITRE technique reference data, and demo users (one per role) in non-production environments only.
- Audit log table is **append-only**; enforced at the application layer and via DB privileges in production.
