"""Application configuration.

All settings are sourced from environment variables (or a local ``.env`` file).
No secrets are hardcoded. See ``.env.example`` at the repo root for the full list.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "staging", "production"]


class Settings(BaseSettings):
    """Strongly-typed application settings loaded from the environment."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── General ──
    environment: Environment = "development"
    debug: bool = True
    project_name: str = "ThreatMind AI"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    log_json: bool = False

    # ── API server ──
    backend_host: str = "0.0.0.0"  # noqa: S104 - bind-all is intended in containers
    backend_port: int = 8000
    backend_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # ── Security / JWT ──
    secret_key: str = "change-me-in-production-use-a-64-char-random-string"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    encryption_key: str = "change-me-generate-a-fernet-key"
    mfa_issuer: str = "ThreatMind AI"
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # ── PostgreSQL ──
    postgres_user: str = "threatmind"
    postgres_password: str = "threatmind_dev_password"
    postgres_db: str = "threatmind"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    database_url: str | None = None  # explicit override wins

    # ── Redis ──
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_url: str | None = None

    # ── Elasticsearch ──
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_index_prefix: str = "threatmind"

    # ── Ollama (local LLM — free) ──
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    ollama_embedding_model: str = "nomic-embed-text"
    llm_provider: Literal["ollama"] = "ollama"
    llm_temperature: float = 0.1
    llm_request_timeout: int = 120

    # ── Observability ──
    otel_enabled: bool = False
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    prometheus_enabled: bool = True

    # ── Derived / computed ──
    @computed_field  # type: ignore[prop-decorator]
    @property
    def sqlalchemy_dsn(self) -> str:
        """Async SQLAlchemy DSN, honoring an explicit ``database_url`` override."""
        if self.database_url:
            return self.database_url
        dsn = PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            path=self.postgres_db,
        )
        return str(dsn)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def redis_dsn(self) -> str:
        if self.redis_url:
            return self.redis_url
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @field_validator("secret_key", "encryption_key")
    @classmethod
    def _warn_on_default_secret(cls, v: str, info: object) -> str:
        # Validation that secrets are changed in production happens at startup
        # (see app.main.lifespan) where we have the full settings context.
        return v

    def assert_production_safe(self) -> None:
        """Fail fast if running in production with insecure defaults."""
        if not self.is_production:
            return
        problems: list[str] = []
        if self.debug:
            problems.append("DEBUG must be false in production")
        if "change-me" in self.secret_key:
            problems.append("SECRET_KEY must be set to a strong random value")
        if "change-me" in self.encryption_key:
            problems.append("ENCRYPTION_KEY must be a real Fernet key")
        if problems:
            raise RuntimeError(
                "Insecure production configuration: " + "; ".join(problems)
            )


@lru_cache
def get_settings() -> Settings:
    """Return the cached singleton settings instance."""
    return Settings()


settings = get_settings()
