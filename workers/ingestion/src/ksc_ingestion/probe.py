"""Live probe of one official URL — the only network path in Phase 7.

A probe asks the official site for one URL with the identified client and
reports what came back. It never stores the body as a record (ingestion goes
through capture bundles) and never retries around a challenge. With
`record=True` a blocked or failed probe is persisted as an ingestion job item
so the access-control situation is visible in the data, not only in a terminal.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from ksc_api.models.enums import IngestionItemStatus
from ksc_ingestion.capture import DiscoveryFailure
from ksc_ingestion.fetch import (
    AccessControlBlockedError,
    FetchError,
    HttpFetcher,
    RobotsDisallowedError,
)
from ksc_ingestion.pipeline import Ingestor
from ksc_ingestion.sources import classify

JOB_TYPE_LIVE_PROBE = "live_probe"


@dataclass(frozen=True)
class ProbeResult:
    url: str
    reachable: bool
    status: IngestionItemStatus | None
    evidence: str
    http_status: int | None = None
    content_type: str | None = None
    byte_size: int | None = None
    probed_at: datetime | None = None

    def as_failure(self) -> DiscoveryFailure | None:
        if self.reachable or self.status is None:
            return None
        classified = classify(self.url)
        return DiscoveryFailure(
            item_key=f"{classified.source_system.value}:probe:{self.url}",
            status=self.status,
            reason=self.evidence,
            detail={
                "url": self.url,
                "url_kind": classified.kind.value,
                "http_status": self.http_status,
                "probed_at": (self.probed_at or datetime.now(UTC)).isoformat(),
            },
        )


def probe(url: str, fetcher: HttpFetcher) -> ProbeResult:
    classify(url)  # raises for anything off the official hosts
    now = datetime.now(UTC)
    try:
        result = fetcher.get(url)
    except AccessControlBlockedError as exc:
        return ProbeResult(
            url,
            False,
            IngestionItemStatus.BLOCKED_BY_ACCESS_CONTROL,
            exc.evidence,
            probed_at=now,
        )
    except RobotsDisallowedError as exc:
        return ProbeResult(
            url, False, IngestionItemStatus.BLOCKED_BY_ACCESS_CONTROL, str(exc), probed_at=now
        )
    except FetchError as exc:
        return ProbeResult(url, False, IngestionItemStatus.FAILED_DOWNLOAD, str(exc), probed_at=now)
    return ProbeResult(
        url,
        True,
        None,
        f"HTTP {result.status_code} {result.content_type or ''}".strip(),
        http_status=result.status_code,
        content_type=result.content_type,
        byte_size=len(result.body),
        probed_at=result.fetched_at,
    )


def record_probe(ingestor: Ingestor, result: ProbeResult) -> str | None:
    """Persist a blocked / failed probe as a one-item job. Returns the job id,
    or None when the probe succeeded (nothing to record)."""

    failure = result.as_failure()
    if failure is None:
        return None
    outcome = ingestor.run_records(
        [failure],
        job_type=JOB_TYPE_LIVE_PROBE,
        source_system=classify(result.url).source_system,
        cursor={"url": result.url, "probed_at": failure.detail["probed_at"]},
        resume=False,
    )
    return outcome.job_id
