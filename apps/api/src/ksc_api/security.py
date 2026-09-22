"""Least-privilege bearer authorization for beta/operator API actions."""

from __future__ import annotations

import hashlib
import hmac
import time
from collections.abc import Callable, Generator
from enum import IntEnum
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis import Redis
from redis.exceptions import RedisError

from ksc_api.config import Settings, get_settings


class Role(IntEnum):
    RESEARCHER = 1
    VERIFIER = 2
    ADMINISTRATOR = 3


_bearer = HTTPBearer(auto_error=False)


def _tokens(settings: Settings) -> dict[Role, tuple[str, ...]]:
    return {
        Role.RESEARCHER: tuple(
            filter(None, map(str.strip, settings.researcher_api_keys.split(",")))
        ),
        Role.VERIFIER: tuple(filter(None, map(str.strip, settings.verifier_api_keys.split(",")))),
        Role.ADMINISTRATOR: tuple(
            filter(None, map(str.strip, settings.administrator_api_keys.split(",")))
        ),
    }


def _authorize(
    required: Role,
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
    settings: Settings,
) -> Role:
    if not settings.privileged_auth_required:
        return Role.ADMINISTRATOR
    if credentials is None or credentials.scheme.casefold() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "privileged bearer token required")
    granted: Role | None = None
    for role, candidates in _tokens(settings).items():
        if any(hmac.compare_digest(credentials.credentials, candidate) for candidate in candidates):
            granted = role
            break
    if granted is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid privileged bearer token")
    if granted < required:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "insufficient role")
    _enforce_rate_limit(request, credentials.credentials, settings)
    return granted


def _enforce_rate_limit(request: Request, token: str, settings: Settings) -> None:
    window = int(time.time() // 60)
    fingerprint = hashlib.sha256(token.encode()).hexdigest()[:16]
    key = f"ksc:privileged:{fingerprint}:{request.url.path}:{window}"
    try:
        client = Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
        count = client.incr(key)
        if count == 1:
            client.expire(key, 70)
    except RedisError as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "authorization rate limiter unavailable"
        ) from exc
    if count > settings.privileged_rate_limit_per_minute:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "privileged request rate exceeded")


def require_role(required: Role) -> Callable[..., Role]:
    def dependency(
        request: Request,
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
        settings: Annotated[Settings, Depends(get_settings)],
    ) -> Role:
        return _authorize(required, request, credentials, settings)

    return dependency


Researcher = Annotated[Role, Depends(require_role(Role.RESEARCHER))]
Verifier = Annotated[Role, Depends(require_role(Role.VERIFIER))]
Administrator = Annotated[Role, Depends(require_role(Role.ADMINISTRATOR))]


def require_ai_capacity(
    _: Researcher, settings: Annotated[Settings, Depends(get_settings)]
) -> Generator[None, None, None]:
    """Bound external/provider work across API processes with a short Redis lease."""
    client = Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
    key = "ksc:ai:concurrent"
    try:
        count = client.incr(key)
        client.expire(key, int(settings.ai_timeout_seconds) + 30)
        if count > settings.ai_max_concurrent_runs:
            client.decr(key)
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "AI concurrency limit reached")
        yield
    except RedisError as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "AI capacity control unavailable"
        ) from exc
    finally:
        try:
            if "count" in locals() and count <= settings.ai_max_concurrent_runs:
                client.decr(key)
        except RedisError:
            pass


AiCapacity = Annotated[None, Depends(require_ai_capacity)]
