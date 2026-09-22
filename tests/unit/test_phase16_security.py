from __future__ import annotations

from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError

from ksc_api.config import Settings
from ksc_api.security import Role, _authorize

TOKENS = {
    "researcher_api_keys": "r" * 32,
    "verifier_api_keys": "v" * 32,
    "administrator_api_keys": "a" * 32,
}


def production_settings(**overrides: object) -> Settings:
    values: Any = {
        "app_env": "production",
        "canonical_url": "https://records.example.org",
        "cors_origins": "https://records.example.org",
        "database_url": "postgresql+psycopg://app:secret@db/ksc?sslmode=verify-full",
        "minio_secure": True,
        "minio_access_key": "production-service-account",
        "minio_secret_key": "s" * 32,
        "redis_url": "redis://:password@redis:6379/0",
        **TOKENS,
        **overrides,
    }
    return Settings(_env_file=None, **values)


def test_production_configuration_rejects_development_defaults() -> None:
    with pytest.raises(ValidationError, match="invalid production configuration"):
        Settings(_env_file=None, app_env="production")

    with pytest.raises(ValidationError, match="CASE_ID"):
        production_settings(case_id="KSC-DEMO-0000")


def test_external_ai_requires_explicit_allowlisted_https_configuration() -> None:
    with pytest.raises(ValidationError, match="AI_EXTERNAL_ENABLED"):
        production_settings(ai_provider="openai_compatible", openai_api_key="secret")
    with pytest.raises(ValidationError, match="AI_ALLOWED_HOSTS"):
        production_settings(
            ai_provider="openai_compatible",
            ai_external_enabled=True,
            openai_api_key="secret",
            openai_compatible_url="http://127.0.0.1/internal",
        )


def test_role_hierarchy_denies_missing_and_underprivileged_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = production_settings()
    request = Mock()
    request.url.path = "/api/v1/appeal/issues/x/review"
    monkeypatch.setattr("ksc_api.security._enforce_rate_limit", lambda *args: None)

    with pytest.raises(HTTPException) as missing:
        _authorize(Role.VERIFIER, request, None, settings)
    assert missing.value.status_code == 401

    researcher = HTTPAuthorizationCredentials(scheme="Bearer", credentials="r" * 32)
    with pytest.raises(HTTPException) as insufficient:
        _authorize(Role.VERIFIER, request, researcher, settings)
    assert insufficient.value.status_code == 403

    verifier = HTTPAuthorizationCredentials(scheme="Bearer", credentials="v" * 32)
    assert _authorize(Role.VERIFIER, request, verifier, settings) is Role.VERIFIER
