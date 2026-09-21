"""Operator capture bundles (docs/ingestion/OPERATOR_CAPTURE.md).

A bundle is a directory the operator filled from a normal browser session on
the official site: saved pages, downloaded PDFs and a `manifest.json` that
records the official URL of every file. This module validates the bundle and
turns it into `DiscoveredRecord`s. It never contacts the network.

Metadata for a record comes, in order of preference, from
1. a parser for the saved official detail page (`DetailPageParser`), which
   yields `MetadataSource.OFFICIAL_PAGE`; or
2. the manifest's `metadata` block (`OPERATOR_MANIFEST`, or
   `SYNTHETIC_FIXTURE` for test bundles — never a real record).
If neither is available the record is a visible `invalid_metadata` failure.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ksc_api.models.enums import DocumentVersionType, IngestionItemStatus, Party
from ksc_ingestion.discovery import (
    DiscoveredArtifact,
    DiscoveredRecord,
    HearingInfo,
    MetadataSource,
)
from ksc_ingestion.normalize import parse_date
from ksc_ingestion.sources import (
    CASE_NUMBER_PATTERN,
    ClassifiedUrl,
    NotOfficialSourceError,
    UrlKind,
    canonicalize,
    classify,
    normalize_language,
)

CAPTURE_FETCH_METHOD = "operator_browser_capture"


class BundleError(ValueError):
    """The bundle as a whole is unusable (missing manifest, bad JSON, unsafe
    paths, non-official URLs). Nothing from it is ingested."""


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ManifestPage(_Model):
    url: str
    file: str
    captured_at: datetime | None = None


class ManifestHearing(_Model):
    date: date
    session_sequence: int = Field(default=1, ge=1)
    session_label: str | None = None
    hearing_type: str | None = None


class ManifestMetadata(_Model):
    """Operator- or fixture-supplied metadata. Values are copied verbatim into
    `source_records.raw_metadata` so the quality gate can see them."""

    metadata_source: Literal["operator_manifest", "capture_snapshot", "synthetic_fixture"] = (
        "operator_manifest"
    )
    record_type: str
    official_ref: str
    title: str
    case_number: str
    external_record_id: str | None = None
    language: str | None = None
    filing_party_label: str | None = None
    filing_party: Party | None = None
    document_date: str | None = None
    filing_date: str | None = None
    public_date: str | None = None
    classification: str | None = None
    hearing: ManifestHearing | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class ManifestArtifact(_Model):
    url: str
    file: str | None = None
    official_version_ref: str | None = None
    version_type: DocumentVersionType | None = None
    version_label: str | None = None
    language: str | None = None
    classification: str | None = None
    public_date: str | None = None
    captured_at: datetime | None = None
    # Recorded at capture time for the official bytes; verified before storing.
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    byte_size: int | None = Field(default=None, ge=0)


class ManifestRecord(_Model):
    detail_page_url: str
    detail_page_file: str | None = None
    listing_url: str | None = None
    artifacts: list[ManifestArtifact] = Field(default_factory=list)
    selection_reason: str | None = None
    captured_at: datetime | None = None
    metadata: ManifestMetadata | None = None


class CaptureManifest(_Model):
    bundle_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    case_number: str = Field(pattern=rf"^{CASE_NUMBER_PATTERN}$")
    captured_by: str = Field(min_length=1)
    captured_at: datetime
    capture_method: str = Field(min_length=1)
    browser: str | None = None
    listing_pages: list[ManifestPage] = Field(default_factory=list)
    records: list[ManifestRecord] = Field(default_factory=list)

    @field_validator("captured_at")
    @classmethod
    def _aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("captured_at must carry a timezone offset")
        return value


@dataclass(frozen=True)
class CaptureBundle:
    root: Path
    manifest: CaptureManifest

    def resolve(self, relative: str) -> Path:
        """A file inside the bundle. Paths that escape the bundle are refused."""

        candidate = (self.root / relative).resolve()
        if self.root.resolve() not in candidate.parents:
            raise BundleError(f"path escapes the bundle: {relative!r}")
        return candidate


@dataclass(frozen=True)
class DiscoveryFailure:
    item_key: str
    status: IngestionItemStatus
    reason: str
    detail: dict[str, Any]


class DetailPageParser(Protocol):
    """Parser for a saved official detail page. Implemented once real pages
    have been captured; the interface is fixed here so the pipeline does not
    change when it lands."""

    def can_parse(self, url: ClassifiedUrl) -> bool: ...

    def parse(self, html: bytes, url: ClassifiedUrl, *, case_number: str) -> ManifestMetadata: ...


def load_bundle(root: Path) -> CaptureBundle:
    root = Path(root)
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise BundleError(f"no manifest.json in {root}")
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise BundleError(f"manifest.json unreadable: {exc}") from exc
    try:
        manifest = CaptureManifest.model_validate(data)
    except ValueError as exc:
        raise BundleError(f"manifest.json invalid: {exc}") from exc

    bundle = CaptureBundle(root=root, manifest=manifest)
    _validate_bundle(bundle)
    return bundle


def load_inventory(path: Path) -> CaptureBundle:
    """Load a metadata-only official inventory manifest.

    The schema intentionally matches capture manifests so a later lawful
    browser capture can fill the same records without a translation layer.
    Inventory files may never name local HTML/PDF files.
    """

    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        manifest = CaptureManifest.model_validate(data)
    except (OSError, ValueError) as exc:
        raise BundleError(f"inventory unreadable or invalid: {exc}") from exc
    if manifest.capture_method != "official_metadata_inventory":
        raise BundleError("inventory capture_method must be official_metadata_inventory")
    if any(page.file for page in manifest.listing_pages):
        raise BundleError("inventory listing pages must not reference local files")
    if any(
        record.detail_page_file or any(artifact.file for artifact in record.artifacts)
        for record in manifest.records
    ):
        raise BundleError("inventory must be metadata-only; local files are not accepted")
    if any(
        record.metadata is not None and record.metadata.metadata_source == "synthetic_fixture"
        for record in manifest.records
    ):
        raise BundleError("synthetic_fixture metadata is forbidden in an official inventory")
    bundle = CaptureBundle(root=path.parent, manifest=manifest)
    # Validate every source/artifact URL and duplicate identity, without any
    # network request or artifact access.
    _validate_bundle(bundle)
    return bundle


def _validate_bundle(bundle: CaptureBundle) -> None:
    """Bundle-level gates: every URL official, every referenced file present
    and inside the bundle, no duplicate detail pages."""

    m = bundle.manifest
    problems: list[str] = []
    for page in m.listing_pages:
        try:
            classify(page.url)
        except NotOfficialSourceError as exc:
            problems.append(str(exc))
        if not bundle.resolve(page.file).is_file():
            problems.append(f"listing page file missing: {page.file}")
    seen: set[str] = set()
    for record in m.records:
        try:
            canonical = canonicalize(record.detail_page_url)
        except NotOfficialSourceError as exc:
            problems.append(str(exc))
            continue
        if canonical in seen:
            problems.append(f"detail page listed twice: {canonical}")
        seen.add(canonical)
        if record.detail_page_file and not bundle.resolve(record.detail_page_file).is_file():
            problems.append(f"detail page file missing: {record.detail_page_file}")
        for artifact in record.artifacts:
            try:
                classify(artifact.url)
            except NotOfficialSourceError as exc:
                problems.append(str(exc))
            if artifact.file and not bundle.resolve(artifact.file).is_file():
                problems.append(f"artifact file missing: {artifact.file}")
    if problems:
        raise BundleError("; ".join(problems))


def _external_record_id(url: ClassifiedUrl, metadata: ManifestMetadata | None) -> str | None:
    if url.kind is UrlKind.PCR_DETAIL and url.doc_id:
        return url.doc_id
    if metadata and metadata.external_record_id:
        return metadata.external_record_id
    return None


def _metadata_for(
    bundle: CaptureBundle,
    record: ManifestRecord,
    url: ClassifiedUrl,
    parsers: Sequence[DetailPageParser],
) -> tuple[ManifestMetadata | None, MetadataSource | None, str | None]:
    """(metadata, its source, problem). Official page first, manifest second."""

    if record.detail_page_file:
        for parser in parsers:
            if parser.can_parse(url):
                html = bundle.resolve(record.detail_page_file).read_bytes()
                parsed = parser.parse(html, url, case_number=bundle.manifest.case_number)
                return parsed, MetadataSource.OFFICIAL_PAGE, None
    if record.metadata is not None:
        return record.metadata, MetadataSource(record.metadata.metadata_source), None
    if record.detail_page_file:
        return (
            None,
            None,
            "saved detail page present but no parser can read it yet and no manifest metadata given",
        )
    return None, None, "no saved detail page and no manifest metadata"


def discover(
    bundle: CaptureBundle, *, parsers: Iterable[DetailPageParser] = ()
) -> list[DiscoveredRecord | DiscoveryFailure]:
    """Turn the bundle into discovered records, in manifest order. Records
    that cannot be described without guessing become `DiscoveryFailure`s so
    the job still shows them."""

    parsers = tuple(parsers)
    m = bundle.manifest
    default_listing = m.listing_pages[0].url if m.listing_pages else None
    out: list[DiscoveredRecord | DiscoveryFailure] = []

    for record in m.records:
        url = classify(record.detail_page_url)
        canonical = canonicalize(record.detail_page_url)
        metadata, source, problem = _metadata_for(bundle, record, url, parsers)
        external_id = _external_record_id(url, metadata)
        provisional_key = f"{url.source_system.value}:{external_id or canonical}"
        if metadata is None or source is None:
            out.append(
                DiscoveryFailure(
                    provisional_key,
                    IngestionItemStatus.INVALID_METADATA,
                    problem or "metadata unavailable",
                    {"detail_page_url": canonical},
                )
            )
            continue
        if external_id is None:
            out.append(
                DiscoveryFailure(
                    provisional_key,
                    IngestionItemStatus.INVALID_METADATA,
                    "no stable external record id (not a PCR detail URL and none given)",
                    {"detail_page_url": canonical},
                )
            )
            continue

        captured_at = record.captured_at or m.captured_at
        artifacts = tuple(
            DiscoveredArtifact(
                url=a.url,
                official_version_ref=a.official_version_ref,
                version_type=a.version_type,
                version_label=a.version_label,
                language=normalize_language(a.language),
                classification=a.classification,
                public_date=parse_date(a.public_date),
                local_file=bundle.resolve(a.file) if a.file else None,
                captured_at=a.captured_at or captured_at,
                fetch_method=CAPTURE_FETCH_METHOD if a.file else None,
                declared_sha256=a.sha256,
                declared_byte_size=a.byte_size,
            )
            for a in record.artifacts
        )
        raw: dict[str, Any] = {
            "capture": {
                "bundle_id": m.bundle_id,
                "captured_by": m.captured_by,
                "capture_method": m.capture_method,
                "browser": m.browser,
                "captured_at": captured_at.isoformat(),
                "detail_page_file": record.detail_page_file,
                "selection_reason": record.selection_reason,
            },
            "metadata_source": source.value,
            "metadata": metadata.model_dump(mode="json", exclude_none=True),
            "detail_url_as_observed": record.detail_page_url,
        }
        hearing = None
        if metadata.hearing is not None:
            hearing = HearingInfo(
                hearing_date=metadata.hearing.date,
                session_sequence=metadata.hearing.session_sequence,
                session_label=metadata.hearing.session_label,
                hearing_type=metadata.hearing.hearing_type,
            )
        out.append(
            DiscoveredRecord(
                source_system=url.source_system,
                external_record_id=external_id,
                record_type=metadata.record_type,
                case_number=metadata.case_number,
                title=metadata.title,
                discovery_url=record.listing_url or default_listing or canonical,
                detail_page_url=canonical,
                metadata_source=source,
                official_ref=metadata.official_ref,
                language=normalize_language(metadata.language) or normalize_language(url.lang),
                filing_party=metadata.filing_party,
                filing_party_label=metadata.filing_party_label,
                document_date=parse_date(metadata.document_date),
                filing_date=parse_date(metadata.filing_date),
                public_date=parse_date(metadata.public_date),
                classification=metadata.classification,
                artifacts=artifacts,
                hearing=hearing,
                raw_metadata=raw,
                discovered_at=captured_at,
                selection_reason=record.selection_reason,
            )
        )
    return out
