"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Central configuration sourced from environment variables."""

    # Application
    app_name: str = "nexlayer"
    app_env: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "postgresql+asyncpg://nexlayer:nexlayer_secret@localhost:5432/nexlayer"

    # JWT
    jwt_secret_key: str = Field(default="CHANGE_ME")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # API Keys (comma-separated)
    api_keys: str = ""

    # AI Provider Credentials
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    local_llm_endpoint: str = "http://localhost:11434"

    # Rate Limiting
    rate_limit_requests_per_minute: int = 60

    # OpenTelemetry
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "nexlayer"

    # Policy
    policy_config_path: str = "config/policies.yaml"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def valid_api_keys(self) -> set[str]:
        if not self.api_keys:
            return set()
        return {k.strip() for k in self.api_keys.split(",") if k.strip()}


def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
