"""Application settings. All configuration comes from the environment."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    log_level: str = "INFO"
    # "json" (structured, one object per line) or "text" for local reading.
    log_format: str = "json"
    # The case is a deployment constant, not a route segment (ROUTE_MAP.md §1).
    case_id: str = "KSC-BC-2020-06"

    api_host: str = "0.0.0.0"  # noqa: S104 - container default, overridden by env
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    database_url: str = "postgresql+psycopg://ksc:ksc_dev_password@localhost:5432/ksc"
    redis_url: str = "redis://localhost:6379/0"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "ksc_minio"
    minio_secret_key: str = "ksc_minio_dev_password"  # noqa: S105 - dev default only
    minio_secure: bool = False
    minio_bucket_documents: str = "ksc-documents"

    # The offline extractive provider is the safe default and needs no secret.
    # External compatible endpoints are opt-in; credentials are never persisted.
    ai_provider: str = "deterministic"
    ai_model: str = "citation-first-extractive-v1"
    ai_temperature: float = Field(default=0.0, ge=0, le=1)
    ai_prompt_dir: str = "packages/prompts"
    openai_api_key: str = ""
    openai_compatible_url: str = "https://api.openai.com/v1/chat/completions"
    anthropic_api_key: str = ""
    anthropic_compatible_url: str = "https://api.anthropic.com/v1/messages"

    # Populated by the container build / CI. Never required.
    git_sha: str = Field(default="unknown", alias="GIT_SHA")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
