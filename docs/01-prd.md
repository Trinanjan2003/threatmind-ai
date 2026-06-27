# ThreatMind AI — Product Requirements Document (PRD)

**Status:** Living document · **Owner:** Product Management · **Audience:** Engineering, Design, SOC stakeholders

---

## 1. Problem statement

Security analysts in a modern SOC are overwhelmed. For every alert they must manually:

- Investigate the triggering event and surrounding context.
- Correlate logs across endpoints, network, identity, and cloud.
- Look up threat intelligence for observed indicators (IOCs).
- Map observed behavior to the MITRE ATT&CK framework.
- Reconstruct the attack timeline.
- Write an incident report and recommend remediation.

This is slow, repetitive, and error-prone. Alert fatigue leads to missed true positives and analyst burnout. The mean time to investigate (MTTI) and mean time to respond (MTTR) are unacceptably high.

## 2. Vision

**ThreatMind AI is an autonomous AI analyst that works alongside the human SOC team.** It ingests security telemetry, hunts for threats continuously, correlates evidence into coherent incidents, and produces analyst-quality investigations and reports — with every conclusion backed by cited evidence and a confidence score. Analysts shift from manual grunt-work to reviewing, directing, and approving AI-driven investigations.

## 3. Goals & non-goals

### Goals
- Reduce MTTI and MTTR by automating investigation and correlation.
- Produce explainable, evidence-backed findings (no black-box verdicts).
- Support the heterogeneous data sources a real SOC already uses.
- Run entirely on free, local, open-source infrastructure (no vendor lock-in, no per-seat cost).
- Deliver a premium analyst experience comparable to commercial SOC platforms.

### Non-goals (initially)
- Active response / automated containment of endpoints (we *recommend* remediation; execution is out of scope for v1).
- Replacing the SIEM or EDR — ThreatMind ingests from them and augments them.
- Multi-tenant SaaS billing (the platform is self-hosted and free).

## 4. Target users & personas

| Persona | Role | Primary needs |
|---|---|---|
| **Priya — Security Analyst (Tier 1/2)** | Triages and investigates alerts | Fast context, AI-suggested next steps, evidence she can trust, less manual correlation |
| **Marcus — SOC Manager** | Owns SOC outcomes & staffing | Queue health, MTTR/MTTI metrics, coverage gaps, audit trail |
| **Dana — Detection Engineer** | Builds & tunes detections | Auto-generated Sigma/YARA/Suricata/SPL/KQL, false-positive feedback loop |
| **Sam — Super Admin / Platform Owner** | Operates the platform | User & role management, integrations, system health, security config |
| **Riley — Read-Only Stakeholder (e.g. auditor, exec)** | Consumes results | Dashboards and reports without the ability to change anything |

## 5. User stories (selected)

**Investigation**
- As an Analyst, I can ask *"Why was this alert generated?"* and get a plain-language explanation with the evidence chain.
- As an Analyst, I can say *"Investigate host WIN-001"* and receive a correlated summary of suspicious activity on that host.
- As an Analyst, I can ask *"Find ransomware behavior"* or *"Show suspicious PowerShell activity"* and get ranked findings with confidence scores.

**Threat hunting**
- As an Analyst, I can launch an autonomous hunt over a time range and data scope, and review the agents' findings.
- As an Analyst, every finding shows its MITRE ATT&CK mapping, confidence score, and the raw evidence that supports it.

**Attack reconstruction**
- As an Analyst, I can view a visual attack timeline (Initial Access → Execution → … → Exfiltration) for an incident.

**Detection engineering**
- As a Detection Engineer, I can turn a confirmed finding into a Sigma/YARA/Suricata rule or a Splunk/KQL query with one action.

**Operations & governance**
- As a SOC Manager, I can see queue volume, MTTI/MTTR, and detection coverage on a dashboard.
- As a Super Admin, I can manage users, roles, and integrations, and review a complete audit log.
- As any user, my access is governed by RBAC and protected by MFA.

## 6. Functional requirements

1. **Data ingestion** from the supported sources (see §8), via file upload and connector APIs, normalized to a common event schema (ECS-inspired).
2. **Detection** combining deterministic rules and AI analysis, producing alerts with severity, confidence, and evidence.
3. **Autonomous threat hunting** via the LangGraph multi-agent engine.
4. **Correlation** of alerts/IOCs/events into incidents.
5. **Attack timeline reconstruction** with MITRE ATT&CK mapping.
6. **AI chat investigation** with streaming, evidence-cited answers.
7. **Detection engineering** rule/query generation.
8. **Incident reporting** export (Markdown/PDF).
9. **Remediation recommendations** per finding.
10. **AuthN/AuthZ**: JWT, OAuth/SSO, MFA, RBAC (4 roles), audit logging.
11. **Observability**: metrics, traces, dashboards.

## 7. Threat detection coverage (v1 target)

Ransomware · Credential Dumping · Privilege Escalation · Persistence · Lateral Movement · Living-off-the-Land (LotL) · Data Exfiltration · Command & Control (C2) · Insider Threats · Cloud Attacks.

Each detection emits: `confidence_score` (0–100), human-readable `explanation`, `evidence[]` (linked raw events), and `mitre_techniques[]`.

## 8. Supported data sources (v1)

Endpoint/host: **Sysmon**, **Windows Event Logs**, **Linux auditd**, **CrowdStrike exports**, generic **EDR exports**.
SIEM: **Microsoft Sentinel**, **Splunk**, **Elastic SIEM**.
Network: **Zeek**, **Suricata**, **Firewall logs**, **DNS logs**, **Proxy logs**.
Cloud: **AWS CloudTrail**, **Azure Activity Logs**, **GCP Audit Logs**.

> Phase 2 ships with two parsers fully implemented (Sysmon, CloudTrail); the rest follow the same `LogParser` interface.

## 9. Roles & permissions (summary)

| Capability | Super Admin | SOC Manager | Analyst | Read-Only |
|---|:--:|:--:|:--:|:--:|
| View dashboards & incidents | ✅ | ✅ | ✅ | ✅ |
| Run investigations / hunts | ✅ | ✅ | ✅ | ❌ |
| Generate detections/rules | ✅ | ✅ | ✅ | ❌ |
| Manage alerts (assign/close) | ✅ | ✅ | ✅ | ❌ |
| Manage data-source connectors | ✅ | ✅ | ❌ | ❌ |
| Manage users & roles | ✅ | ❌ | ❌ | ❌ |
| View audit log | ✅ | ✅ | ❌ | ❌ |
| Configure platform settings | ✅ | ❌ | ❌ | ❌ |

Full matrix in [`06-security-model.md`](06-security-model.md).

## 10. Non-functional requirements

- **Performance:** P95 API latency < 300 ms for interactive endpoints (excluding LLM calls, which stream). Ingestion throughput target: 5k events/sec sustained on commodity hardware.
- **Scalability:** Horizontally scalable stateless API; async workers for ingestion and hunts.
- **Reliability:** Graceful degradation if Ollama/Elasticsearch is unavailable (features disable, app stays up).
- **Security:** See §11 and the security model doc.
- **Accessibility:** WCAG 2.1 AA for the frontend.
- **Portability:** Runs on macOS, Windows, Linux.
- **Test coverage:** ≥ 80% on backend domain + application layers.

## 11. Security & compliance posture

JWT access/refresh tokens, OAuth2/OIDC SSO, TOTP MFA, RBAC, full audit logging, per-client rate limiting, encryption in transit (TLS) and at rest (Fernet-encrypted sensitive fields + encrypted volumes). Aligns conceptually with SOC 2 / ISO 27001 control families (access control, audit, encryption) — formal certification out of scope for the OSS project.

## 12. Success metrics

- ↓ Median MTTI by ≥ 50% vs. manual baseline (measured in pilot).
- ↓ MTTR by ≥ 30%.
- ≥ 90% of AI findings rated "useful" or "actionable" by analysts.
- ≥ 80% automated triage on ingested alerts (auto-enriched + scored before human touch).

## 13. Assumptions & dependencies

- A local Ollama instance with at least one pulled model is available.
- Customers export or stream telemetry from their existing tools.
- Commodity hardware with enough RAM to run the chosen Ollama model.

## 14. Out of scope (v1) / future

Automated containment & response (SOAR playbook execution), UEBA baselining ML models, multi-tenant deployments, mobile app, marketplace of community detections.
