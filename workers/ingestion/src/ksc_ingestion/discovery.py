"""Discovery contract: what any source (parsed official page, capture manifest,
future live listing) must produce for the pipeline to persist a record.

`DiscoveredRecord` is the normalized picture of one official record *as the
source presented it* — with the URLs it was seen at — before anything is
fetched or written. `DiscoveredArtifact` is one public file the record links
to. Neither carries document text.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from ksc_api.models.enums import DocumentVersionType, Party, SourceSystem, Visibility


class MetadataSource(enum.StrEnum):
    """Where the record's metadata came from. The quality gate reads this."""

    OFFICIAL_PAGE = "official_page"  # parsed from a saved / fetched official page
    # Normalised snapshot of the official detail page, built inside the
    # browser session from the fields the page publishes (not the raw DOM).
    CAPTURE_SNAPSHOT = "capture_snapshot"
    OPERATOR_MANIFEST = "operator_manifest"  # typed by the operator into the manifest
    SYNTHETIC_FIXTURE = "synthetic_fixture"  # test data; never a real record


@dataclass(frozen=True)
class DiscoveredArtifact:
    # Official artifact URL as observed. Never constructed.
    url: str
    official_version_ref: str | None = None
    version_type: DocumentVersionType | None = None
    version_label: str | None = None
    language: str | None = None
    # Classification text as the source shows it ("Public", "Public Redacted",
    # "Confidential"); visibility is derived from it, fail closed.
    classification: str | None = None
    public_date: date | None = None
    # Captured bytes, when the operator saved the file. None → metadata only.
    local_file: Path | None = None
    captured_at: datetime | None = None
    fetch_method: str | None = None
    # Hash / size the capture recorded for the official bytes, when known. The
    # pipeline refuses to store a file that does not match them.
    declared_sha256: str | None = None
    declared_byte_size: int | None = None


@dataclass(frozen=True)
class HearingInfo:
    hearing_date: date
    session_sequence: int = 1
    session_label: str | None = None
    hearing_type: str | None = None


@dataclass(frozen=True)
class DiscoveredRecord:
    source_system: SourceSystem
    # The source's own key: PCR doc_id, hearing slug, …
    external_record_id: str
    record_type: str
    case_number: str
    title: str
    # Where it was seen (listing / bundle) and its canonical detail page.
    discovery_url: str
    detail_page_url: str
    metadata_source: MetadataSource
    official_ref: str | None = None
    language: str | None = None
    filing_party: Party | None = None
    filing_party_label: str | None = None
    document_date: date | None = None
    filing_date: date | None = None
    public_date: date | None = None
    classification: str | None = None
    artifacts: tuple[DiscoveredArtifact, ...] = ()
    hearing: HearingInfo | None = None
    raw_metadata: dict[str, Any] = field(default_factory=dict)
    discovered_at: datetime | None = None
    selection_reason: str | None = None

    @property
    def item_key(self) -> str:
        return f"{self.source_system.value}:{self.external_record_id}"


def visibility_from_classification(classification: str | None) -> Visibility:
    """Public-only gate. Only an explicit public classification opens it;
    anything confidential, sealed or ex parte — or nothing at all — closes it."""

    if classification is None:
        return Visibility.UNKNOWN
    text = " ".join(classification.lower().split())
    if not text:
        return Visibility.UNKNOWN
    closed_markers = ("confidential", "ex parte", "under seal", "sealed", "not public")
    if any(marker in text for marker in closed_markers) and "public" not in text:
        return Visibility.NOT_PUBLIC
    if text.startswith(("strictly confidential", "confidential")):
        # "Confidential ... with public annex" describes the record itself as confidential.
        return Visibility.NOT_PUBLIC
    if "public redacted" in text or "public-redacted" in text:
        return Visibility.PUBLIC_REDACTED
    if "public" in text:
        return Visibility.PUBLIC
    return Visibility.UNKNOWN
