"""Application settings.

All configuration comes from the environment (see `.env.example`). No AI provider
key is required — Phase 4 makes no AI calls.
"""

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

    # Populated by the container build / CI. Never required.
    git_sha: str = Field(default="unknown", alias="GIT_SHA")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
