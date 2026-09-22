"""Strict manual-URL import and real-data audit for Phase 14."""

from __future__ import annotations

import hashlib
import ipaddress
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from ksc_api.models import (
    COMPARISON_CLASSES,
    COURT_MEDIA_STATUSES,
    AiRetrievalSource,
    Case,
    CourtMediaLink,
    ExternalSource,
    MediaItem,
    MediaStatement,
    MediaStatementComparison,
    ResolutionState,
    VerificationState,
)


class MediaManifestError(ValueError):
    pass


def _canonical_url(raw: str) -> str:
    parsed = urlsplit(raw.strip())
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise MediaManifestError("external URLs must be public HTTPS URLs without credentials")
    host = parsed.hostname.casefold()
    if host in {"localhost", "127.0.0.1"} or host.endswith(".local"):
        raise MediaManifestError("local/private URLs are not external public sources")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        if not address.is_global:
            raise MediaManifestError("local/private URLs are not external public sources")
    return urlunsplit(("https", parsed.netloc.casefold(), parsed.path or "/", parsed.query, ""))


def _time(raw: str | None) -> datetime | None:
    if raw is None:
        return None
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MediaManifestError("timestamps must be ISO 8601 values") from exc
    if value.tzinfo is None:
        raise MediaManifestError("timestamps must include a timezone")
    return value


def load_media_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("items"), list):
        raise MediaManifestError("unsupported Phase 14 manifest")
    if len(data["items"]) < 1:
        raise MediaManifestError("manifest contains no public items")
    keys: set[str] = set()
    urls: set[str] = set()
    for item in data["items"]:
        key = item.get("key")
        if not isinstance(key, str) or not key or key in keys:
            raise MediaManifestError("item keys must be non-empty and unique")
        keys.add(key)
        url = _canonical_url(item["canonical_url"])
        _canonical_url(item["original_url"])
        _canonical_url(item["source_canonical_url"])
        if item.get("archive_url"):
            _canonical_url(item["archive_url"])
        if url in urls:
            raise MediaManifestError(f"duplicate canonical URL: {url}")
        urls.add(url)
        if item.get("access_status") != "public" or item.get("visibility") != "public":
            raise MediaManifestError(f"{key}: only explicitly public material is accepted")
        if item.get("access_method") not in {
            "manual_url",
            "public_webpage",
            "official_api",
            "operator_capture",
        }:
            raise MediaManifestError(f"{key}: unsupported access method")
        if (
            not str(item.get("terms_note") or "").strip()
            or not str(item.get("coverage_note") or "").strip()
        ):
            raise MediaManifestError(f"{key}: terms and coverage notes are required")
        court_status = item.get("court_status", "external_only")
        if court_status not in COURT_MEDIA_STATUSES:
            raise MediaManifestError(f"{key}: unsupported court status")
        if court_status not in {"external_only", "unknown"}:
            raise MediaManifestError(
                f"{key}: a stronger court status requires the reviewed exact-citation workflow"
            )
        published = _time(item.get("published_at"))
        captured = _time(item.get("captured_at"))
        if captured is None or (published is not None and captured < published):
            raise MediaManifestError(f"{key}: invalid publication/capture timestamps")
        text = item.get("captured_text")
        if not isinstance(text, str) or not text.strip():
            raise MediaManifestError(f"{key}: captured text is required")
        expected = hashlib.sha256(text.encode()).hexdigest()
        if item.get("content_sha256") != expected:
            raise MediaManifestError(f"{key}: content hash mismatch")
        for statement in item.get("statements", []):
            if statement.get("text") not in text:
                raise MediaManifestError(f"{key}: statement is not an exact captured-text span")
    comparison_keys: set[str] = set()
    for comparison in data.get("comparisons", []):
        key = comparison.get("key")
        if not isinstance(key, str) or not key or key in comparison_keys:
            raise MediaManifestError("comparison keys must be non-empty and unique")
        comparison_keys.add(key)
        if comparison.get("classification") not in COMPARISON_CLASSES:
            raise MediaManifestError(f"{key}: unsupported comparison classification")
        if comparison.get("item_a") not in keys or comparison.get("item_b") not in keys:
            raise MediaManifestError(f"{key}: comparison item anchor is missing")
    return cast(dict[str, Any], data)


@dataclass(frozen=True)
class MediaImportResult:
    sources: int
    items: int
    statements: int
    court_links: int
    comparisons: int


def import_media_manifest(session: Session, case: Case, path: Path) -> MediaImportResult:
    data = load_media_manifest(path)
    reviewer = str(data.get("reviewed_by") or "phase14-review")
    reviewed_at = _time(data.get("reviewed_at")) or datetime.now(UTC)
    by_key: dict[str, MediaItem] = {}

    # The controlled manifest is authoritative for this bounded Phase 14 set.
    existing_ids = list(session.scalars(select(MediaItem.id).where(MediaItem.case_id == case.id)))
    if existing_ids:
        session.execute(
            delete(MediaStatementComparison).where(MediaStatementComparison.case_id == case.id)
        )
        session.execute(delete(CourtMediaLink).where(CourtMediaLink.case_id == case.id))
        session.execute(
            delete(MediaStatement).where(MediaStatement.media_item_id.in_(existing_ids))
        )
        session.execute(delete(MediaItem).where(MediaItem.case_id == case.id))
    session.execute(delete(ExternalSource).where(ExternalSource.case_id == case.id))
    session.flush()

    sources: dict[str, ExternalSource] = {}
    statement_count = 0
    for raw in data["items"]:
        source_url = _canonical_url(raw["source_canonical_url"])
        source = sources.get(source_url)
        if source is None:
            source = ExternalSource(
                case_id=case.id,
                platform=raw["platform"],
                source_type=raw["source_type"],
                publisher=raw["publisher"],
                account=raw.get("account"),
                canonical_url=source_url,
                visibility="public",
                access_method=raw["access_method"],
                language=raw["language"],
                terms_note=raw["terms_note"],
                coverage_note=raw["coverage_note"],
                verification_state=VerificationState.HUMAN_VERIFIED,
                verified_by=reviewer,
                verified_at=reviewed_at,
            )
            session.add(source)
            session.flush()
            sources[source_url] = source
        item = MediaItem(
            case_id=case.id,
            external_source_id=source.id,
            canonical_url=_canonical_url(raw["canonical_url"]),
            original_url=_canonical_url(raw["original_url"]),
            title=raw["title"],
            publisher=raw["publisher"],
            published_at=_time(raw.get("published_at")),
            captured_at=_time(raw["captured_at"]),
            language=raw["language"],
            content_sha256=raw["content_sha256"],
            transcript_origin=raw.get("transcript_origin"),
            item_kind=raw.get("item_kind", "original"),
            archive_url=(_canonical_url(raw["archive_url"]) if raw.get("archive_url") else None),
            access_status="public",
            captured_text=raw["captured_text"],
            source_metadata=raw.get("source_metadata", {}),
            verification_state=VerificationState.HUMAN_VERIFIED,
            verified_by=reviewer,
            verified_at=reviewed_at,
        )
        session.add(item)
        session.flush()
        by_key[raw["key"]] = item
        for sequence, statement in enumerate(raw.get("statements", []), 1):
            text = statement["text"]
            start = raw["captured_text"].index(text)
            session.add(
                MediaStatement(
                    media_item_id=item.id,
                    sequence=sequence,
                    speaker=statement.get("speaker"),
                    text=text,
                    text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                    exact_quote=True,
                    char_from=start,
                    char_to=start + len(text),
                    transcript_origin=statement.get("transcript_origin", "publisher_webpage"),
                    verification_state=VerificationState.HUMAN_VERIFIED,
                    verified_by=reviewer,
                    verified_at=reviewed_at,
                )
            )
            statement_count += 1
        session.add(
            CourtMediaLink(
                case_id=case.id,
                media_item_id=item.id,
                court_status=raw.get("court_status", "external_only"),
                note=raw.get(
                    "court_status_note", "No court-record relationship has been established."
                ),
                verification_state=VerificationState.HUMAN_VERIFIED,
                verified_by=reviewer,
                verified_at=reviewed_at,
            )
        )
    session.flush()

    comparison_count = 0
    for raw in data.get("comparisons", []):
        a = session.scalar(
            select(MediaStatement).where(
                MediaStatement.media_item_id == by_key[raw["item_a"]].id,
                MediaStatement.sequence == raw.get("statement_a", 1),
            )
        )
        b = session.scalar(
            select(MediaStatement).where(
                MediaStatement.media_item_id == by_key[raw["item_b"]].id,
                MediaStatement.sequence == raw.get("statement_b", 1),
            )
        )
        if a is None or b is None:
            raise MediaManifestError("comparison statement anchor is missing")
        session.add(
            MediaStatementComparison(
                case_id=case.id,
                comparison_key=raw["key"],
                title=raw["title"],
                classification=raw["classification"],
                statement_a_id=a.id,
                statement_b_id=b.id,
                explanation=raw["explanation"],
                extraction_origin="human_reviewed_manifest",
                verification_state=VerificationState.HUMAN_VERIFIED,
                verified_by=reviewer,
                verified_at=reviewed_at,
            )
        )
        comparison_count += 1
    session.commit()
    return MediaImportResult(
        len(sources), len(by_key), statement_count, len(by_key), comparison_count
    )


@dataclass(frozen=True)
class Phase14GateReport:
    generated_at: str
    real_public_sources: int
    real_public_items: int
    exact_statements: int
    court_links: int
    citation_backed_court_links: int
    invalid_court_links: int
    comparisons: int
    duplicate_urls: int
    manifest_item_mismatches: int
    verification_violations: int
    ai_external_retrieval_sources: int
    access_violations: int
    coverage_limitations_documented: bool
    passed: bool


def run_phase14_gate(
    session: Session, case: Case, manifest_path: Path, generated_at: str
) -> Phase14GateReport:
    manifest = load_media_manifest(manifest_path)
    items = list(
        session.scalars(
            select(MediaItem)
            .options(
                selectinload(MediaItem.source),
                selectinload(MediaItem.statements),
                selectinload(MediaItem.court_links).selectinload(CourtMediaLink.citation),
            )
            .where(MediaItem.case_id == case.id)
        )
    )
    links = [link for item in items for link in item.court_links]
    invalid_links = sum(
        link.court_status not in {"external_only", "unknown"}
        and (
            link.citation is None
            or link.citation.case_id != case.id
            or link.citation.resolution_state != ResolutionState.RESOLVED
            or link.verification_state != VerificationState.HUMAN_VERIFIED
        )
        for link in links
    )
    exact = sum(
        statement.exact_quote
        and statement.text in item.captured_text
        and statement.text_sha256 == hashlib.sha256(statement.text.encode()).hexdigest()
        for item in items
        for statement in item.statements
    )
    duplicate_urls = len(items) - len({item.canonical_url for item in items})
    access_violations = sum(
        item.access_status != "public" or item.source.visibility != "public" for item in items
    )
    ai_external = int(
        session.scalar(
            select(func.count())
            .select_from(AiRetrievalSource)
            .where(AiRetrievalSource.source_category == "external_public_source")
        )
        or 0
    )
    comparison_rows = list(
        session.scalars(
            select(MediaStatementComparison)
            .options(
                selectinload(MediaStatementComparison.statement_a).selectinload(
                    MediaStatement.item
                ),
                selectinload(MediaStatementComparison.statement_b).selectinload(
                    MediaStatement.item
                ),
            )
            .where(MediaStatementComparison.case_id == case.id)
        )
    )
    comparisons = len(comparison_rows)
    sources = len({item.external_source_id for item in items})
    manifest_urls = {_canonical_url(item["canonical_url"]) for item in manifest["items"]}
    database_urls = {item.canonical_url for item in items}
    manifest_mismatches = len(manifest_urls.symmetric_difference(database_urls))
    item_ids = {item.id for item in items}
    verification_rows: list[Any] = []
    for item in items:
        verification_rows.extend((item.source, item, *item.statements, *item.court_links))
    verification_violations = sum(
        row.verification_state != VerificationState.HUMAN_VERIFIED for row in verification_rows
    ) + sum(
        comparison.verification_state != VerificationState.HUMAN_VERIFIED
        or comparison.statement_a.item.id not in item_ids
        or (comparison.statement_b is not None and comparison.statement_b.item.id not in item_ids)
        for comparison in comparison_rows
    )
    limitations = all(bool(item.source.coverage_note.strip()) for item in items) and bool(
        manifest.get("coverage_limitations")
    )
    passed = all(
        (
            sources >= 2,
            len(items) >= 3,
            exact >= 3,
            len(links) == len(items),
            invalid_links == 0,
            comparisons >= 1,
            duplicate_urls == 0,
            manifest_mismatches == 0,
            verification_violations == 0,
            ai_external == 0,
            access_violations == 0,
            limitations,
        )
    )
    return Phase14GateReport(
        generated_at=generated_at,
        real_public_sources=sources,
        real_public_items=len(items),
        exact_statements=exact,
        court_links=len(links),
        citation_backed_court_links=sum(link.citation_id is not None for link in links),
        invalid_court_links=invalid_links,
        comparisons=comparisons,
        duplicate_urls=duplicate_urls,
        manifest_item_mismatches=manifest_mismatches,
        verification_violations=verification_violations,
        ai_external_retrieval_sources=ai_external,
        access_violations=access_violations,
        coverage_limitations_documented=limitations,
        passed=passed,
    )


def write_phase14_report(report: Phase14GateReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
