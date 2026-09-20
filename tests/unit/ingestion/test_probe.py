"""A probe reports a challenge as a blocked, recordable failure."""

from __future__ import annotations

import httpx
import pytest

from ksc_api.models.enums import IngestionItemStatus
from ksc_ingestion.fetch import HttpFetcher
from ksc_ingestion.probe import probe
from ksc_ingestion.sources import NotOfficialSourceError

URL = (
    "https://repository.scp-ks.org/details.php?doc_id=091ec6e98038f36c&doc_type=stl_filing&lang=eng"
)


def _fetcher(response: httpx.Response) -> HttpFetcher:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        return response

    return HttpFetcher(transport=httpx.MockTransport(handler), min_interval=0)


def test_blocked_probe_is_a_visible_access_control_failure() -> None:
    challenge = httpx.Response(
        403,
        content=b"<html>Just a moment...</html>",
        headers={"cf-mitigated": "challenge", "content-type": "text/html"},
    )
    with _fetcher(challenge) as f:
        result = probe(URL, f)
    assert not result.reachable
    assert result.status is IngestionItemStatus.BLOCKED_BY_ACCESS_CONTROL
    failure = result.as_failure()
    assert failure is not None
    assert failure.status is IngestionItemStatus.BLOCKED_BY_ACCESS_CONTROL
    assert failure.item_key == f"ksc_public_court_records:probe:{URL}"
    assert failure.detail["url_kind"] == "pcr_detail"
    assert "cf-mitigated" in failure.reason


def test_http_error_probe_is_a_failed_download() -> None:
    with _fetcher(httpx.Response(500)) as f:
        result = probe(URL, f)
    assert result.status is IngestionItemStatus.FAILED_DOWNLOAD


def test_reachable_probe_records_nothing() -> None:
    with _fetcher(
        httpx.Response(200, content=b"<html>ok</html>", headers={"content-type": "text/html"})
    ) as f:
        result = probe(URL, f)
    assert result.reachable
    assert result.as_failure() is None
    assert result.http_status == 200


def test_probe_refuses_non_official_urls() -> None:
    with _fetcher(httpx.Response(200)) as f, pytest.raises(NotOfficialSourceError):
        probe("https://example.com/", f)
