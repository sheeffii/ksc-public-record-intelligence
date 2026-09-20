"""The fetcher identifies itself, obeys robots, paces requests and treats a
bot-mitigation challenge as a closed door — never as something to work around."""

from __future__ import annotations

import httpx
import pytest

from ksc_ingestion.fetch import (
    DEFAULT_USER_AGENT,
    AccessControlBlockedError,
    FetchError,
    HttpFetcher,
    RobotsDisallowedError,
    looks_like_challenge,
)

HOST = "https://repository.scp-ks.org"
CHALLENGE_HTML = (
    b"<!DOCTYPE html><html><head><title>Just a moment...</title></head>"
    b'<body><script src="https://challenges.cloudflare.com/x"></script></body></html>'
)


class Site:
    """Scripted origin. Records every request so tests can prove there was
    exactly one attempt and no header games."""

    def __init__(self, routes: dict[str, httpx.Response]) -> None:
        self.routes = routes
        self.requests: list[httpx.Request] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        key = request.url.path + (f"?{request.url.query.decode()}" if request.url.query else "")
        if key in self.routes:
            return self.routes[key]
        return httpx.Response(404)

    def fetcher(self, **kwargs: object) -> HttpFetcher:
        return HttpFetcher(
            transport=httpx.MockTransport(self.handler),
            min_interval=0,
            **kwargs,  # type: ignore[arg-type]
        )


def robots(text: str = "User-agent: *\nAllow: /\n") -> httpx.Response:
    return httpx.Response(200, text=text, headers={"content-type": "text/plain"})


def test_identified_user_agent_and_successful_fetch() -> None:
    site = Site({"/robots.txt": robots(), "/page": httpx.Response(200, content=b"%PDF-1.4 x")})
    with site.fetcher() as f:
        result = f.get(f"{HOST}/page")
    assert result.body.startswith(b"%PDF-")
    assert result.status_code == 200
    assert all(r.headers["user-agent"] == DEFAULT_USER_AGENT for r in site.requests)
    assert "ksc-public-record-intelligence" in DEFAULT_USER_AGENT
    assert "contact:" in DEFAULT_USER_AGENT
    assert "Mozilla" not in DEFAULT_USER_AGENT


def test_cf_mitigated_header_is_an_access_control_and_is_not_retried() -> None:
    site = Site(
        {
            "/robots.txt": robots(),
            "/page": httpx.Response(
                403,
                content=CHALLENGE_HTML,
                headers={"cf-mitigated": "challenge", "content-type": "text/html"},
            ),
        }
    )
    with site.fetcher() as f, pytest.raises(AccessControlBlockedError) as exc:
        f.get(f"{HOST}/page")
    assert "cf-mitigated: challenge" in exc.value.evidence
    assert [r.url.path for r in site.requests] == ["/robots.txt", "/page"]


def test_challenge_page_without_header_is_detected_by_body() -> None:
    assert looks_like_challenge(403, httpx.Headers({"content-type": "text/html"}), CHALLENGE_HTML)
    assert looks_like_challenge(503, httpx.Headers({"content-type": "text/html"}), CHALLENGE_HTML)
    assert not looks_like_challenge(
        403, httpx.Headers({"content-type": "text/html"}), b"<p>forbidden</p>"
    )
    assert not looks_like_challenge(
        200, httpx.Headers({"content-type": "text/html"}), CHALLENGE_HTML
    )


def test_challenged_robots_closes_the_whole_host() -> None:
    site = Site(
        {
            "/robots.txt": httpx.Response(
                403,
                content=CHALLENGE_HTML,
                headers={"cf-mitigated": "challenge", "content-type": "text/html"},
            ),
            "/page": httpx.Response(200, content=b"ok"),
        }
    )
    with site.fetcher() as f:
        with pytest.raises(AccessControlBlockedError):
            f.get(f"{HOST}/page")
        with pytest.raises(AccessControlBlockedError):
            f.get(f"{HOST}/other")
    # robots once; nothing else was ever requested from the closed host
    assert [r.url.path for r in site.requests] == ["/robots.txt"]


def test_unreadable_robots_fails_closed() -> None:
    site = Site({"/robots.txt": httpx.Response(500), "/page": httpx.Response(200, content=b"ok")})
    with site.fetcher() as f, pytest.raises(AccessControlBlockedError):
        f.get(f"{HOST}/page")
    assert [r.url.path for r in site.requests] == ["/robots.txt"]


def test_missing_robots_allows_but_disallow_rule_is_honoured() -> None:
    site = Site({"/page": httpx.Response(200, content=b"ok")})
    with site.fetcher() as f:
        assert f.get(f"{HOST}/page").status_code == 200
    site = Site(
        {"/robots.txt": robots("User-agent: *\nDisallow: /LW/\n"), "/LW/x.pdf": httpx.Response(200)}
    )
    with site.fetcher() as f, pytest.raises(RobotsDisallowedError):
        f.get(f"{HOST}/LW/x.pdf")
    assert [r.url.path for r in site.requests] == ["/robots.txt"]


def test_redirect_off_official_hosts_is_refused() -> None:
    site = Site(
        {
            "/robots.txt": robots(),
            "/page": httpx.Response(302, headers={"location": "https://example.com/elsewhere"}),
        }
    )
    with site.fetcher() as f, pytest.raises(FetchError, match="off official hosts"):
        f.get(f"{HOST}/page")


def test_http_error_is_a_fetch_error_not_a_challenge() -> None:
    site = Site({"/robots.txt": robots(), "/page": httpx.Response(404)})
    with site.fetcher() as f, pytest.raises(FetchError, match="HTTP 404"):
        f.get(f"{HOST}/page")


def test_requests_to_one_host_are_paced() -> None:
    waited: list[float] = []
    clock = iter([0.0, 0.0, 1.0, 1.0, 1.5, 1.5, 100.0, 100.0])
    site = Site({"/robots.txt": robots(), "/a": httpx.Response(200), "/b": httpx.Response(200)})
    f = HttpFetcher(
        transport=httpx.MockTransport(site.handler),
        min_interval=5.0,
        sleep=waited.append,
        clock=lambda: next(clock),
    )
    f.get(f"{HOST}/a")
    f.get(f"{HOST}/b")
    assert waited and all(w > 0 for w in waited)


def test_non_official_url_never_hits_the_network() -> None:
    site = Site({})
    with site.fetcher() as f, pytest.raises(Exception, match="not an official"):
        f.get("https://example.com/")
    assert site.requests == []
