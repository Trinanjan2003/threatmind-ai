# ════════════════════════════════════════════════════════════════
#  ThreatMind AI — developer task runner (macOS / Linux)
#  Windows users: use scripts/dev.ps1 (mirrors these targets).
# ════════════════════════════════════════════════════════════════
.DEFAULT_GOAL := help
.PHONY: help setup up down logs ps restart \
        backend-install backend-dev backend-lint backend-fmt backend-test \
        frontend-install frontend-dev frontend-build frontend-lint \
        db-migrate db-revision db-seed clean

# ─── Meta ─────────────────────────────────────────────────────
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

setup: ## Copy .env, build images, pull Ollama model
	@test -f .env || cp .env.example .env
	docker compose build
	@echo "Now run: make up   (then 'ollama pull llama3.1' if running Ollama natively)"

# ─── Docker Compose stack ─────────────────────────────────────
up: ## Start the full stack in the background
	docker compose up -d

down: ## Stop the stack
	docker compose down

restart: ## Restart the stack
	docker compose restart

logs: ## Tail logs from all services
	docker compose logs -f

ps: ## Show running services
	docker compose ps

# ─── Backend ──────────────────────────────────────────────────
backend-install: ## Install backend deps into a venv
	cd backend && python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"

backend-dev: ## Run the FastAPI dev server with reload
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

backend-lint: ## Lint + type-check backend
	cd backend && ruff check . && mypy app

backend-fmt: ## Auto-format backend
	cd backend && ruff format . && ruff check --fix .

backend-test: ## Run backend tests with coverage
	cd backend && pytest --cov=app --cov-report=term-missing --cov-report=html

# ─── Frontend ─────────────────────────────────────────────────
frontend-install: ## Install frontend deps
	cd frontend && npm install

frontend-dev: ## Run the Next.js dev server
	cd frontend && npm run dev

frontend-build: ## Production build of the frontend
	cd frontend && npm run build

frontend-lint: ## Lint frontend
	cd frontend && npm run lint

# ─── Database ─────────────────────────────────────────────────
db-migrate: ## Apply all DB migrations
	cd backend && alembic upgrade head

db-revision: ## Create a new migration (usage: make db-revision m="message")
	cd backend && alembic revision --autogenerate -m "$(m)"

db-seed: ## Seed initial data (roles, demo users)
	cd backend && python -m app.scripts.seed

# ─── Housekeeping ─────────────────────────────────────────────
clean: ## Remove caches and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/htmlcov frontend/.next frontend/out
