# ThreatMind AI — Delivery Roadmap

This platform is built in **vertical slices**: each phase delivers something that actually runs end-to-end, rather than a layer of scaffolding that only works once everything else exists. A slice touches the database, backend, and (where relevant) the UI together.

## Guiding principles

- **Free & local only.** Ollama for all AI inference. No paid APIs, no billing code, ever.
- **Cross-platform.** macOS, Windows, Linux. Infra via Docker Compose; helper scripts for both `make` and PowerShell.
- **Production posture, incremental scope.** Clean architecture, tests, and observability are built in from the start — we grow features, not quality shortcuts.

## Phases

| Phase | Title | Outcome | Status |
|------:|-------|---------|--------|
| **0** | Foundation | Repo, architecture docs, Docker Compose, FastAPI clean-architecture skeleton, auth + RBAC | 🟡 In progress |
| **1** | Frontend shell & design system | Next.js + Tailwind + shadcn + Framer Motion. Dark/light, dashboard layout, navigation, design tokens. Mocked data. | ⬜ Planned |
| **2** | Ingestion & detection vertical | Ingest Sysmon + CloudTrail → normalize → rule-based detections → alerts persisted → live dashboard view with real charts | ⬜ Planned |
| **3** | AI multi-agent engine | LangGraph orchestration of the 8 agents, shared memory (Redis), Ollama provider, autonomous hunt runs | ⬜ Planned |
| **4** | AI chat investigation | Natural-language investigation workspace with streaming answers + cited evidence | ⬜ Planned |
| **5** | Detection engineering + MITRE + timeline | Sigma/YARA/Suricata/SPL/KQL generation, MITRE ATT&CK matrix viz, attack-timeline reconstruction | ⬜ Planned |
| **6** | Hardening & delivery | 80%+ test coverage, Prometheus/Grafana/OTel, K8s manifests, GitHub Actions CI/CD | ⬜ Planned |

## Definition of done (per phase)

- Code runs locally via Docker Compose **and** natively (documented for mac + Windows).
- New endpoints documented in OpenAPI and `docs/04-api-design.md`.
- Unit + integration tests for new logic; coverage does not regress.
- Lint (ruff/eslint) and type checks (mypy/tsc) pass.
- Docs updated for any new concept or workflow.
