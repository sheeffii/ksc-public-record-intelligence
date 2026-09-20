"""Identified, rate-limited HTTP fetcher for official KSC URLs.

Behaviour that is deliberately fixed (docs/SECURITY.md, ADR-011):

- only `sources.OFFICIAL_HOSTS`, https only, redirects only within them;
- an identifying User-Agent with a contact address; never a browser string;
- robots.txt is consulted first. If robots.txt itself cannot be read (blocked,
  challenged, server error) the host is treated as closed — nothing else on it
  is requested;
- a bot-mitigation challenge (Cloudflare `cf-mitigated: challenge`, or a
  403/503 page pointing at challenges.cloudflare.com) raises
  `AccessControlBlockedError`. It is never retried with different headers, cookies,
  a browser engine or a proxy. The caller records a visible failure;
- at most one request per `min_interval` seconds per host.

Observed 2026-09-20: every official surface challenged this client. The
fetcher therefore exists for probing and for a future in which the court site
admits identified research clients — not because Phase 7 fetches with it.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from urllib import robotparser
from urllib.parse import urlsplit

import httpx

from ksc_ingestion import __version__
from ksc_ingestion.sources import OFFICIAL_HOSTS, require_official

log = logging.getLogger(__name__)

DEFAULT_USER_AGENT = (
    f"ksc-public-record-intelligence/{__version__} "
    "(+research tool over the public court record; identified client; "
    "contact: shefqetsalihu123@gmail.com)"
)
_CHALLENGE_MARKERS = (b"challenges.cloudflare.com", b"cf-chl", b"Just a moment...")


class FetchError(RuntimeError):
    """A request could not be completed (network, timeout, HTTP error)."""


class AccessControlBlockedError(FetchError):
    """The host answered with a bot-mitigation challenge or refused robots.txt.
    This is an access control. It is reported, never worked around."""

    def __init__(self, url: str, evidence: str) -> None:
        super().__init__(f"access control blocked {url}: {evidence}")
        self.url = url
        self.evidence = evidence


class RobotsDisallowedError(FetchError):
    """robots.txt disallows this path for our user agent."""


@dataclass(frozen=True)
class FetchResult:
    url: str
    final_url: str
    status_code: int
    content_type: str | None
    body: bytes
    fetched_at: datetime
    headers: dict[str, str] = field(default_factory=dict, repr=False)


def looks_like_challenge(status_code: int, headers: httpx.Headers, body: bytes) -> str | None:
    """Return the evidence string if the response is a bot-mitigation
    challenge rather than the requested resource, else None."""

    mitigated = headers.get("cf-mitigated")
    if mitigated:
        return f"cf-mitigated: {mitigated}"
    if status_code in (403, 429, 503):
        content_type = headers.get("content-type", "")
        if "text/html" in content_type:
            head = body[:20000]
            for marker in _CHALLENGE_MARKERS:
                if marker in head:
                    return f"HTTP {status_code} challenge page ({marker.decode()})"
    return None


class HttpFetcher:
    """One instance per run. Holds the robots cache and per-host pacing."""

    def __init__(
        self,
        *,
        user_agent: str = DEFAULT_USER_AGENT,
        min_interval: float = 5.0,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.user_agent = user_agent
        self.min_interval = min_interval
        self._sleep = sleep or time.sleep
        self._clock = clock or time.monotonic
        self._last_request_at: dict[str, float] = {}
        self._robots: dict[str, robotparser.RobotFileParser | None] = {}
        self._client = httpx.Client(
            headers={
                "User-Agent": user_agent,
                "Accept": "text/html,application/pdf;q=0.9,*/*;q=0.5",
            },
            timeout=timeout,
            follow_redirects=False,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> HttpFetcher:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ----------------------------------------------------------- internals --
    def _pace(self, host: str) -> None:
        last = self._last_request_at.get(host)
        if last is not None:
            wait = self.min_interval - (self._clock() - last)
            if wait > 0:
                self._sleep(wait)
        self._last_request_at[host] = self._clock()

    def _raw_get(self, url: str) -> httpx.Response:
        host = (urlsplit(url).hostname or "").lower()
        self._pace(host)
        try:
            response = self._client.get(url)
        except httpx.HTTPError as exc:
            raise FetchError(f"{type(exc).__name__} fetching {url}") from exc
        evidence = looks_like_challenge(response.status_code, response.headers, response.content)
        if evidence:
            log.warning("access control challenge at %s (%s)", url, evidence)
            raise AccessControlBlockedError(url, evidence)
        return response

    def robots_for(self, host: str) -> robotparser.RobotFileParser:
        """robots.txt for the host, fetched once. Fails closed: unreadable
        robots → AccessControlBlockedError for the whole host."""

        if host in self._robots:
            cached = self._robots[host]
            if cached is None:
                raise AccessControlBlockedError(
                    f"https://{host}/robots.txt", "robots.txt unavailable"
                )
            return cached
        robots_url = f"https://{host}/robots.txt"
        parser = robotparser.RobotFileParser(robots_url)
        try:
            response = self._raw_get(robots_url)
        except AccessControlBlockedError:
            self._robots[host] = None
            raise
        if response.status_code == 404:
            parser.parse([])  # no robots file: nothing disallowed
        elif response.status_code == 200:
            parser.parse(response.text.splitlines())
        else:
            self._robots[host] = None
            raise AccessControlBlockedError(robots_url, f"robots.txt HTTP {response.status_code}")
        self._robots[host] = parser
        return parser

    # ------------------------------------------------------------- public --
    def get(self, url: str, *, max_redirects: int = 3) -> FetchResult:
        url = require_official(url)
        current = url
        for _ in range(max_redirects + 1):
            host = (urlsplit(current).hostname or "").lower()
            robots = self.robots_for(host)
            if not robots.can_fetch(self.user_agent, current):
                raise RobotsDisallowedError(f"robots.txt disallows {current}")
            response = self._raw_get(current)
            if response.is_redirect:
                location = response.headers.get("location", "")
                target = str(httpx.URL(current).join(location))
                if (urlsplit(target).hostname or "").lower() not in OFFICIAL_HOSTS:
                    raise FetchError(f"redirect off official hosts refused: {current} → {target}")
                current = target
                continue
            if response.status_code >= 400:
                raise FetchError(f"HTTP {response.status_code} fetching {current}")
            return FetchResult(
                url=url,
                final_url=current,
                status_code=response.status_code,
                content_type=response.headers.get("content-type"),
                body=response.content,
                fetched_at=datetime.now(UTC),
                headers=dict(response.headers),
            )
        raise FetchError(f"too many redirects from {url}")
