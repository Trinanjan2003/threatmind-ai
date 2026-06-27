# ════════════════════════════════════════════════════════════════
#  ThreatMind AI — developer task runner (Windows / PowerShell)
#  Mirrors the Makefile. Usage:  .\scripts\dev.ps1 <command> [args]
#  Example:  .\scripts\dev.ps1 up
# ════════════════════════════════════════════════════════════════
param(
    [Parameter(Position = 0)]
    [string]$Command = "help",
    [Parameter(Position = 1)]
    [string]$Arg = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

function Invoke-InDir($dir, $script) {
    Push-Location (Join-Path $Root $dir)
    try { & $script } finally { Pop-Location }
}

switch ($Command.ToLower()) {
    "help" {
        Write-Host "ThreatMind AI dev commands:" -ForegroundColor Cyan
        @(
            "  setup            Copy .env and build images",
            "  up               Start the full stack",
            "  down             Stop the stack",
            "  logs             Tail logs",
            "  ps               Show running services",
            "  backend-install  Create venv + install backend deps",
            "  backend-dev      Run FastAPI dev server",
            "  backend-test     Run backend tests with coverage",
            "  frontend-install Install frontend deps",
            "  frontend-dev     Run Next.js dev server",
            "  db-migrate       Apply DB migrations",
            "  db-seed          Seed initial data"
        ) | ForEach-Object { Write-Host $_ }
    }
    "setup" {
        if (-not (Test-Path (Join-Path $Root ".env"))) {
            Copy-Item (Join-Path $Root ".env.example") (Join-Path $Root ".env")
            Write-Host "Created .env from .env.example" -ForegroundColor Green
        }
        Invoke-InDir "." { docker compose build }
        Write-Host "Now run: .\scripts\dev.ps1 up" -ForegroundColor Yellow
    }
    "up"    { Invoke-InDir "." { docker compose up -d } }
    "down"  { Invoke-InDir "." { docker compose down } }
    "logs"  { Invoke-InDir "." { docker compose logs -f } }
    "ps"    { Invoke-InDir "." { docker compose ps } }
    "backend-install" {
        Invoke-InDir "backend" {
            python -m venv .venv
            .\.venv\Scripts\Activate.ps1
            pip install -e ".[dev]"
        }
    }
    "backend-dev"  { Invoke-InDir "backend" { uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 } }
    "backend-test" { Invoke-InDir "backend" { pytest --cov=app --cov-report=term-missing } }
    "frontend-install" { Invoke-InDir "frontend" { npm install } }
    "frontend-dev"     { Invoke-InDir "frontend" { npm run dev } }
    "db-migrate"       { Invoke-InDir "backend" { alembic upgrade head } }
    "db-seed"          { Invoke-InDir "backend" { python -m app.scripts.seed } }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host "Run '.\scripts\dev.ps1 help' for the list of commands."
        exit 1
    }
}
