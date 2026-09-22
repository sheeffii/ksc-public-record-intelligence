"""Application settings. All configuration comes from the environment."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["development", "test", "staging", "production"] = "development"
    log_level: str = "INFO"
    # "json" (structured, one object per line) or "text" for local reading.
    log_format: str = "json"
    # The case is a deployment constant, not a route segment (ROUTE_MAP.md §1).
    case_id: str = "KSC-BC-2020-06"

    api_host: str = "0.0.0.0"  # noqa: S104 - container default, overridden by env
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"
    canonical_url: str = "http://localhost:3000"
    max_request_bytes: int = Field(default=10 * 1024 * 1024, ge=1024, le=50 * 1024 * 1024)

    database_url: str = "postgresql+psycopg://ksc:ksc_dev_password@localhost:5432/ksc"
    redis_url: str = "redis://localhost:6379/0"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "ksc_minio"
    minio_secret_key: str = "ksc_minio_dev_password"  # noqa: S105 - dev default only
    minio_secure: bool = False
    minio_bucket_documents: str = "ksc-documents"

    # Comma-separated bearer tokens. These are beta/operator credentials, not
    # browser-visible configuration. Verifier and administrator inherit the
    # permissions below them. Production requires all three scopes.
    researcher_api_keys: str = ""
    verifier_api_keys: str = ""
    administrator_api_keys: str = ""
    privileged_rate_limit_per_minute: int = Field(default=60, ge=1, le=1000)

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
    ai_external_enabled: bool = False
    ai_allowed_hosts: str = "api.openai.com,api.anthropic.com"
    ai_timeout_seconds: float = Field(default=30, ge=1, le=120)
    ai_max_retries: int = Field(default=1, ge=0, le=3)
    ai_max_output_tokens: int = Field(default=1600, ge=128, le=8192)
    ai_max_daily_runs: int = Field(default=100, ge=1, le=10000)
    ai_max_concurrent_runs: int = Field(default=2, ge=1, le=32)

    # Populated by the container build / CI. Never required.
    git_sha: str = Field(default="unknown", alias="GIT_SHA")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def privileged_auth_required(self) -> bool:
        return self.app_env in {"staging", "production"}

    @model_validator(mode="after")
    def validate_deployment_boundary(self) -> Settings:
        if self.app_env not in {"staging", "production"}:
            return self

        errors: list[str] = []
        if self.case_id.startswith("KSC-DEMO"):
            errors.append("CASE_ID may not select a demo fixture")
        canonical = urlparse(self.canonical_url)
        if (
            canonical.scheme != "https"
            or not canonical.netloc
            or canonical.path not in {"", "/"}
            or canonical.query
        ):
            errors.append("CANONICAL_URL must be an absolute HTTPS URL")
        origins = self.cors_origin_list
        if not origins or any(urlparse(origin).scheme != "https" for origin in origins):
            errors.append("CORS_ORIGINS must contain only HTTPS origins")
        if "*" in origins:
            errors.append("CORS_ORIGINS may not contain a wildcard")
        if self.canonical_url.rstrip("/") not in {origin.rstrip("/") for origin in origins}:
            errors.append("CORS_ORIGINS must include CANONICAL_URL")
        database = urlparse(self.database_url)
        if (
            "ksc_dev_password" in self.database_url
            or "sslmode=" not in self.database_url
            or database.username in {None, "postgres", "root"}
        ):
            errors.append("DATABASE_URL must use non-development credentials and declare sslmode")
        if not self.minio_secure:
            errors.append("MINIO_SECURE must be true")
        if self.minio_secret_key in {"", "ksc_minio_dev_password"}:
            errors.append("MINIO_SECRET_KEY must be a non-development secret")
        if self.minio_access_key in {"", "ksc_minio"}:
            errors.append("MINIO_ACCESS_KEY must be a dedicated production identity")
        if not urlparse(self.redis_url).password:
            errors.append("REDIS_URL must include authentication")

        role_values = {
            "RESEARCHER_API_KEYS": self.researcher_api_keys,
            "VERIFIER_API_KEYS": self.verifier_api_keys,
            "ADMINISTRATOR_API_KEYS": self.administrator_api_keys,
        }
        tokens = []
        for name, value in role_values.items():
            keys = [item.strip() for item in value.split(",") if item.strip()]
            if not keys or any(len(item) < 32 for item in keys):
                errors.append(f"{name} must contain token(s) of at least 32 characters")
            tokens.extend(keys)
        if len(tokens) != len(set(tokens)):
            errors.append("privileged API tokens must be unique across roles")

        provider = self.ai_provider.casefold()
        if provider not in {
            "disabled",
            "deterministic",
            "openai_compatible",
            "anthropic_compatible",
        }:
            errors.append("AI_PROVIDER is unsupported")
        if provider not in {"disabled", "deterministic"}:
            if not self.ai_external_enabled:
                errors.append("AI_EXTERNAL_ENABLED must explicitly enable an external provider")
            endpoint = (
                self.openai_compatible_url
                if provider == "openai_compatible"
                else self.anthropic_compatible_url
            )
            parsed = urlparse(endpoint)
            allowed = {item.strip().casefold() for item in self.ai_allowed_hosts.split(",")}
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or parsed.hostname.casefold() not in allowed
            ):
                errors.append("external AI endpoint must be HTTPS and listed in AI_ALLOWED_HOSTS")
            secret = (
                self.openai_api_key if provider == "openai_compatible" else self.anthropic_api_key
            )
            if not secret:
                errors.append("the selected external AI provider secret is required")
        if errors:
            raise ValueError("invalid production configuration: " + "; ".join(errors))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
