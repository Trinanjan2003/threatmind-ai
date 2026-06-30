# ThreatMind AI — Full Setup Guide (macOS · Windows · Linux)

A complete, copy-paste setup from a blank machine to a running app. ThreatMind AI
is an **AI-powered threat-hunting / detection-engineering platform** that runs
**100% free / local** — the only "AI" dependency is **Ollama** (a local LLM
runner). No paid API keys.

Two ways to run it:

| Mode | What runs | When to use |
|---|---|---|
| **Local dev** (recommended to start) | Backend venv + frontend dev server + Ollama | Fastest; just Python + Node + Ollama |
| **Full stack** (Docker) | Postgres + Redis + Ollama + backend + frontend | Production-like; needs Docker Desktop |

---

## 0. Prerequisites (install once)

Need **Python 3.11+**, **Node.js 18+**, **Git**, and **Ollama**. Docker optional.

### macOS

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"   # if no brew
brew install python@3.11 node git ollama
brew install --cask docker    # optional
```

### Windows (PowerShell as Administrator)

```powershell
winget install Python.Python.3.11
winget install OpenJS.NodeJS.LTS
winget install Git.Git
winget install Ollama.Ollama
winget install Docker.DockerDesktop   # optional
```

> Reopen your terminal after installing so the tools are on your PATH.

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm git curl
curl -fsSL https://ollama.com/install.sh | sh
```

---

## 1. Set up Ollama (the local LLM) — all platforms

```bash
ollama serve            # leave running (macOS app auto-starts it)

# in another terminal, pull the models the app uses:
ollama pull llama3.1            # default agent model (~4.7 GB)
ollama pull nomic-embed-text    # embeddings for semantic search / RAG (~280 MB)

ollama list                                  # verify
curl http://localhost:11434/api/tags         # should return JSON
```

> **Low on RAM?** Use `ollama pull llama3.2:3b` and set `OLLAMA_MODEL=llama3.2:3b`
> in `.env`. The 8B model wants ~8 GB free.

---

## 2. Get the code

```bash
git clone https://github.com/Trinanjan2003/threatmind-ai.git
cd threatmind-ai
```

---

## 3. Configure environment

```bash
cp .env.example .env          # macOS / Linux
# copy .env.example .env      # Windows PowerShell
```

Confirm in `.env`:
- `OLLAMA_BASE_URL=http://localhost:11434`
- `OLLAMA_MODEL=llama3.1`
- `OLLAMA_EMBEDDING_MODEL=nomic-embed-text`

Generate secrets and paste them in:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"                       # SECRET_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"   # ENCRYPTION_KEY (if present)
```

---

## 4A. Run locally (no Docker) — recommended

### Backend (terminal 1)

```bash
cd backend
python -m venv .venv

source .venv/bin/activate         # macOS / Linux
# .venv\Scripts\Activate.ps1      # Windows PowerShell
# .venv\Scripts\activate.bat      # Windows cmd

pip install --upgrade pip
pip install -e .                  # installs backend + deps from pyproject.toml

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend → **http://localhost:8000**, docs at **/docs**, health at
**/api/v1/health**.

> Shortcut from repo root: `make backend-install` then `make backend-dev`.

### Frontend (terminal 2)

```bash
cd frontend
npm install
npm run dev
```

Frontend → **http://localhost:3000**.

> Shortcut: `make frontend-install` then `make frontend-dev`.

---

## 4B. Run the full stack (Docker)

```bash
make setup     # copies .env, builds images, pulls the Ollama model
make up        # starts Postgres, Redis, Ollama, backend, frontend
make ps        # status;   make logs  to tail
make db-migrate && make db-seed
```

URLs are the same (frontend :3000, backend :8000). Stop with `make down`.

---

## 5. Verify

```bash
curl http://localhost:8000/api/v1/health
cd backend && source .venv/bin/activate && pytest -q     # test suite
```

Open http://localhost:3000 — you should reach the threat-hunting dashboard,
MITRE ATT&CK matrix, and the AI chat investigation (WebSocket streaming).

---

## 6. Troubleshooting

| Symptom | Fix |
|---|---|
| `ollama: command not found` | Reopen terminal; on Linux run `ollama serve` |
| AI chat hangs | Model still pulling (`ollama list`); or low RAM → `llama3.2:3b` |
| `port 8000 in use` | `uvicorn ... --port 8001`, update `BACKEND_PORT` |
| `pip install -e .` build error | `pip install --upgrade pip setuptools wheel` first |
| Windows activate blocked | `Set-ExecutionPolicy -Scope Process RemoteSigned`, re-activate |
| WebSocket chat won't connect | Confirm backend is up and CORS origins include `localhost:3000` |
| Docker: services unhealthy | Give Docker ≥6 GB RAM in Docker Desktop settings |

---

## 7. What's pending / not done yet

- **No live cloud deployment** — `infra/` has K8s/Helm but the app isn't running
  on a managed cluster (no public URL).
- **Ollama not exercised end-to-end during build** — AI paths are written and
  unit-tested with mocks; a full live run needs Ollama + the model on your box.
- **Full-stack Docker path is config-complete but not CI-validated** on every OS.
- **CI runs lint + tests**, not a full Docker integration boot.
- Later-phase detection content / integrations are scaffolded — see
  `docs/00-roadmap.md` and `docs/12-deliverables-map.md`.

See `docs/11-deployment-guide.md` for the full deployment reference.
