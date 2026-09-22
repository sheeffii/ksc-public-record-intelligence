"""Production observability without new infrastructure (Phase 13).

Two things live here:

* In-process HTTP request metrics (counter by method/route/status and a
  latency histogram by method/route) recorded by the API middleware. Routes
  are the matched templates (``/api/v1/documents/{document_id}``), never raw
  paths, so no identifier or search text ends up in a label.
* Operational gauges read from the database at scrape time: corpus, artifact
  bytes, parser review, citations by resolution state, acquisition queue
  depth and stuck leases, open quarantine, processing runs by state, failed
  ingestion items and AI run outcomes. They are the same numbers the internal
  ingestion status endpoint reports, exposed in Prometheus text format so a
  scraper can alert on them (``ops/alerts/ksc-api.rules.yml``).

The format follows the Prometheus text exposition format (version 0.0.4);
no client library is required.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import Integer, func, select
from sqlalchemy.orm import Session

from ksc_api import __version__
from ksc_api.models import (
    AiRun,
    ArtifactAcquisition,
    ArtifactQuarantine,
    Case,
    ProcessingRun,
)
from ksc_api.repositories.ingestion import IngestionStatusRepository

LATENCY_BUCKETS: tuple[float, ...] = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)


@dataclass
class _Histogram:
    count: int = 0
    total: float = 0.0
    buckets: list[int] = field(default_factory=lambda: [0] * len(LATENCY_BUCKETS))

    def observe(self, seconds: float) -> None:
        self.count += 1
        self.total += seconds
        for index, upper in enumerate(LATENCY_BUCKETS):
            if seconds <= upper:
                self.buckets[index] += 1


class RequestMetrics:
    """Thread-safe in-process request counters and latency histograms."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._requests: dict[tuple[str, str, str], int] = {}
        self._latency: dict[tuple[str, str], _Histogram] = {}
        self.started_at = time.time()

    def record(self, method: str, route: str, status: int, seconds: float) -> None:
        with self._lock:
            key = (method, route, str(status))
            self._requests[key] = self._requests.get(key, 0) + 1
            self._latency.setdefault((method, route), _Histogram()).observe(seconds)

    def reset(self) -> None:
        with self._lock:
            self._requests.clear()
            self._latency.clear()

    def render(self) -> list[str]:
        lines: list[str] = []
        with self._lock:
            lines.append(
                "# HELP ksc_http_requests_total HTTP requests by method, route template and status."
            )
            lines.append("# TYPE ksc_http_requests_total counter")
            for (method, route, status), count in sorted(self._requests.items()):
                lines.append(
                    f'ksc_http_requests_total{{method="{method}",route="{_escape(route)}",status="{status}"}} {count}'
                )
            lines.append(
                "# HELP ksc_http_request_duration_seconds HTTP request latency by method and route."
            )
            lines.append("# TYPE ksc_http_request_duration_seconds histogram")
            for (method, route), hist in sorted(self._latency.items()):
                labels = f'method="{method}",route="{_escape(route)}"'
                for upper, cumulative in zip(LATENCY_BUCKETS, hist.buckets, strict=True):
                    lines.append(
                        f'ksc_http_request_duration_seconds_bucket{{{labels},le="{_fmt(upper)}"}} {cumulative}'
                    )
                lines.append(
                    f'ksc_http_request_duration_seconds_bucket{{{labels},le="+Inf"}} {hist.count}'
                )
                lines.append(f"ksc_http_request_duration_seconds_sum{{{labels}}} {hist.total:.6f}")
                lines.append(f"ksc_http_request_duration_seconds_count{{{labels}}} {hist.count}")
            lines.append("# HELP ksc_process_uptime_seconds Seconds since the API process started.")
            lines.append("# TYPE ksc_process_uptime_seconds gauge")
            lines.append(f"ksc_process_uptime_seconds {time.time() - self.started_at:.3f}")
        return lines


request_metrics = RequestMetrics()


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _fmt(value: float) -> str:
    text = f"{value:g}"
    return text if "." in text or "e" in text else f"{text}.0"


def route_template(scope: Mapping[str, object]) -> str:
    """Matched route template for a request scope, or ``unmatched``."""
    route = scope.get("route")
    path = getattr(route, "path", None)
    return path if isinstance(path, str) else "unmatched"


# ---------------------------------------------------------------- gauges --
@dataclass(frozen=True)
class Gauge:
    name: str
    help: str
    value: float
    labels: tuple[tuple[str, str], ...] = ()

    def render(self) -> str:
        if self.labels:
            labels = ",".join(f'{key}="{_escape(val)}"' for key, val in self.labels)
            return f"{self.name}{{{labels}}} {_fmt_value(self.value)}"
        return f"{self.name} {_fmt_value(self.value)}"


def _fmt_value(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.6f}"


def operational_gauges(session: Session, case_number: str) -> list[Gauge]:
    """Database-backed operational state for the configured case."""
    case = session.scalar(select(Case).where(Case.case_number == case_number))
    if case is None:
        return [Gauge("ksc_case_configured", "1 when the configured case is seeded.", 0)]
    counts = IngestionStatusRepository(session, case).counts()
    now = datetime.now(UTC)
    stuck_leases = int(
        session.scalar(
            select(func.count())
            .select_from(ArtifactAcquisition)
            .where(
                ArtifactAcquisition.case_id == case.id,
                ArtifactAcquisition.status == "leased",
                ArtifactAcquisition.lease_expires_at < now,
            )
        )
        or 0
    )
    runs: dict[str, int] = {
        str(state): int(count)
        for state, count in session.execute(
            select(ProcessingRun.status, func.count())
            .where(ProcessingRun.case_id == case.id)
            .group_by(ProcessingRun.status)
        ).all()
    }
    quarantine: dict[str, int] = {
        str(state): int(count)
        for state, count in session.execute(
            select(ArtifactQuarantine.state, func.count())
            .where(ArtifactQuarantine.case_id == case.id)
            .group_by(ArtifactQuarantine.state)
        ).all()
    }
    ai = session.execute(
        select(
            func.count(),
            func.coalesce(func.sum(func.cast(AiRun.answer_withheld, Integer)), 0),
            func.coalesce(func.sum(func.cast(AiRun.status == "failed", Integer)), 0),
            func.coalesce(func.sum(AiRun.cost_usd), 0),
        ).where(AiRun.case_id == case.id)
    ).one()

    gauges: list[Gauge] = [
        Gauge("ksc_case_configured", "1 when the configured case is seeded.", 1),
        Gauge(
            "ksc_source_records", "Source records discovered for the case.", counts.source_records
        ),
        Gauge("ksc_documents", "Documents for the case.", counts.documents),
        Gauge("ksc_document_versions", "Document versions for the case.", counts.versions),
        Gauge(
            "ksc_versions_fetched",
            "Versions with a verified held artifact.",
            counts.versions_fetched,
        ),
        Gauge(
            "ksc_versions_failed", "Versions whose artifact fetch failed.", counts.versions_failed
        ),
        Gauge("ksc_versions_parsed", "Versions with parser output.", counts.versions_parsed),
        Gauge(
            "ksc_versions_parse_review_required",
            "Versions the parser flagged for review.",
            counts.parse_review_required,
        ),
        Gauge(
            "ksc_verified_artifact_bytes",
            "Bytes of hash-verified held artifacts.",
            counts.verified_artifact_bytes,
        ),
        Gauge("ksc_pages_parsed", "Parsed PDF pages.", counts.pages_parsed),
        Gauge(
            "ksc_transcript_segments_parsed",
            "Parsed transcript segments.",
            counts.transcript_segments_parsed,
        ),
        Gauge("ksc_ingestion_jobs", "Ingestion jobs recorded.", counts.jobs),
        Gauge(
            "ksc_ingestion_items_failed",
            "Ingestion items in a failure state (incl. access-control blocks).",
            counts.items_failed,
        ),
        Gauge(
            "ksc_ingestion_items_duplicate",
            "Ingestion items skipped as identical bytes.",
            counts.items_duplicate,
        ),
        Gauge(
            "ksc_source_metadata_snapshots",
            "Immutable source metadata snapshots.",
            counts.source_metadata_snapshots,
        ),
        Gauge(
            "ksc_acquisition_stuck_leases",
            "Leased acquisitions whose lease has expired.",
            stuck_leases,
        ),
    ]
    for state, value in (
        ("pending", counts.acquisition_pending),
        ("leased", counts.acquisition_leased),
        ("blocked", counts.acquisition_blocked),
        ("failed", counts.acquisition_failed),
    ):
        gauges.append(
            Gauge(
                "ksc_acquisition_queue",
                "Acquisition queue rows by state.",
                value,
                (("state", state),),
            )
        )
    for state, value in (
        ("resolved", counts.citations_resolved),
        ("ambiguous", counts.citations_ambiguous),
        ("unresolved", counts.citations_unresolved),
        ("invalid", counts.citations_invalid),
    ):
        gauges.append(
            Gauge(
                "ksc_citations",
                "Citations by persisted resolution state.",
                value,
                (("state", state),),
            )
        )
    for state in ("open", "released", "rejected"):
        gauges.append(
            Gauge(
                "ksc_quarantine",
                "Artifact quarantine rows by state.",
                int(quarantine.get(state, 0)),
                (("state", state),),
            )
        )
    for state in ("running", "completed", "failed"):
        gauges.append(
            Gauge(
                "ksc_processing_runs",
                "Parser/resolver processing runs by state.",
                int(runs.get(state, 0)),
                (("state", state),),
            )
        )
    gauges.append(Gauge("ksc_ai_runs", "AI research runs recorded.", int(ai[0])))
    gauges.append(
        Gauge(
            "ksc_ai_runs_withheld", "AI runs whose answer was withheld by validation.", int(ai[1])
        )
    )
    gauges.append(Gauge("ksc_ai_runs_failed", "AI runs that failed.", int(ai[2])))
    gauges.append(Gauge("ksc_ai_cost_usd_total", "Recorded AI provider cost in USD.", float(ai[3])))
    return gauges


def render_metrics(gauges: Iterable[Gauge], *, db_scrape_ok: bool, git_sha: str) -> str:
    lines = list(request_metrics.render())
    lines.append("# HELP ksc_build_info Build information.")
    lines.append("# TYPE ksc_build_info gauge")
    lines.append(
        f'ksc_build_info{{version="{_escape(__version__)}",git_sha="{_escape(git_sha)}"}} 1'
    )
    lines.append(
        "# HELP ksc_metrics_db_scrape_ok 1 when the database-backed gauges were read on this scrape."
    )
    lines.append("# TYPE ksc_metrics_db_scrape_ok gauge")
    lines.append(f"ksc_metrics_db_scrape_ok {1 if db_scrape_ok else 0}")
    seen: set[str] = set()
    for gauge in gauges:
        if gauge.name not in seen:
            seen.add(gauge.name)
            lines.append(f"# HELP {gauge.name} {gauge.help}")
            lines.append(f"# TYPE {gauge.name} gauge")
        lines.append(gauge.render())
    return "\n".join(lines) + "\n"
