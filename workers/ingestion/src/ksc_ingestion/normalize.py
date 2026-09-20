"""Normalization of discovered metadata into Document / DocumentVersion fields.

Every rule here is deterministic and conservative: when the source does not say,
the value stays None or fails closed. Nothing infers a date from another date
(DESIGN_DECISIONS.md §7) and nothing invents an identifier.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from ksc_api.models.enums import DocumentVersionType, Party, Visibility
from ksc_ingestion.discovery import (
    DiscoveredArtifact,
    DiscoveredRecord,
    visibility_from_classification,
)
from ksc_ingestion.sources import CASE_NUMBER_PATTERN, CASE_NUMBER_RE

_MONTHS = {
    m: i
    for i, m in enumerate(
        (
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ),
        start=1,
    )
}
_TEXT_DATE_RE = re.compile(
    r"\b(?P<d>\d{1,2})\s+(?P<m>[A-Za-z]+)\s+(?P<y>\d{4})\b",
)
_NUMERIC_DATE_RE = re.compile(r"^(?P<d>\d{1,2})[/.](?P<m>\d{1,2})[/.](?P<y>\d{4})$")
# Direct filing in the case: KSC-BC-2020-06/F00005[/RED][/COR][/A01] …
_DIRECT_FILING_RE = re.compile(rf"^(?P<case>{CASE_NUMBER_PATTERN})/(?P<filing>F\d{{5}})(?:/.*)?$")
_RED_RE = re.compile(r"(?:^|[/\-_ ])RED\d*(?:$|[/\-_ ])")
_COR_RE = re.compile(r"(?:^|[/\-_ ])COR\d*(?:$|[/\-_ ])")


class NormalizationError(ValueError):
    """Metadata cannot be mapped without guessing; the item fails as
    `invalid_metadata` or `ambiguous_mapping` (message says which)."""

    def __init__(self, message: str, *, ambiguous: bool = False) -> None:
        super().__init__(message)
        self.ambiguous = ambiguous


def parse_date(value: str | date | None) -> date | None:
    """ISO `2024-11-25`, PCR-style `25 November 2024`, or `25/11/2024`.
    Anything else → None (never guessed)."""

    if value is None:
        return None
    if isinstance(value, date):
        return value
    text = value.strip()
    if not text:
        return None
    if len(text) >= 10 and text[4] == "-":
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None
    m = _NUMERIC_DATE_RE.match(text)
    if m:
        try:
            return date(int(m["y"]), int(m["m"]), int(m["d"]))
        except ValueError:
            return None
    m = _TEXT_DATE_RE.search(text)
    if m and m["m"].lower() in _MONTHS:
        try:
            return date(int(m["y"]), _MONTHS[m["m"].lower()], int(m["d"]))
        except ValueError:
            return None
    return None


def date_in_text(text: str) -> date | None:
    """First `25 November 2024`-style date in a title (transcript headings)."""

    m = _TEXT_DATE_RE.search(text)
    if m and m["m"].lower() in _MONTHS:
        try:
            return date(int(m["y"]), _MONTHS[m["m"].lower()], int(m["d"]))
        except ValueError:
            return None
    return None


def filing_number(official_ref: str | None) -> str | None:
    """`KSC-BC-2020-06/F00005/RED` → `F00005`. Sub-proceedings
    (`…/IA002/F00001`) return None: the bare number is not unique there."""

    if not official_ref:
        return None
    m = _DIRECT_FILING_RE.match(official_ref.strip())
    return m["filing"] if m else None


_PARTY_MARKERS: tuple[tuple[tuple[str, ...], Party], ...] = (
    (("specialist prosecutor", "prosecution", "spo"), Party.SPO),
    (("defence", "defense"), Party.DEFENCE),
    (("victims' counsel", "victims counsel", "victims\u2019 counsel"), Party.VICTIMS_COUNSEL),
    (
        (
            "trial panel",
            "pre-trial judge",
            "court of appeals",
            "appeals panel",
            "supreme court",
            "president",
            "chamber",
            "panel",
            "judge",
        ),
        Party.COURT,
    ),
)


def party_from_label(label: str | None) -> Party | None:
    """Filing party from the source's own label. Unknown labels → OTHER (the
    label itself is kept on the record); nothing → None."""

    if label is None or not label.strip():
        return None
    text = label.lower()
    for markers, party in _PARTY_MARKERS:
        if any(marker in text for marker in markers):
            return party
    return Party.OTHER


def classify_version_type(
    official_version_ref: str | None,
    title: str | None,
    *,
    artifact_language: str | None,
    record_language: str | None,
) -> DocumentVersionType:
    """Precedence: public redacted > corrected > reclassified > translation >
    original. Suffixes on the official reference win over words in the title."""

    ref = (official_version_ref or "").upper()
    text = (title or "").lower()
    if _RED_RE.search(ref) or "public redacted" in text or "public-redacted" in text:
        return DocumentVersionType.PUBLIC_REDACTED
    if _COR_RE.search(ref) or "corrected version" in text or "corrigendum" in text:
        return DocumentVersionType.CORRECTED
    if "reclassif" in text:
        return DocumentVersionType.RECLASSIFIED
    if artifact_language and record_language and artifact_language != record_language:
        return DocumentVersionType.TRANSLATION
    return DocumentVersionType.ORIGINAL


@dataclass(frozen=True)
class NormalizedVersion:
    official_version_ref: str
    version_type: DocumentVersionType
    version_label: str | None
    visibility: Visibility
    language: str | None
    public_date: date | None
    source_url: str
    artifact: DiscoveredArtifact


@dataclass(frozen=True)
class NormalizedDocument:
    official_ref: str
    filing_number: str | None
    title: str
    document_type: str
    language: str | None
    filing_party: Party | None
    document_date: date | None
    filing_date: date | None
    public_date: date | None
    visibility: Visibility
    versions: tuple[NormalizedVersion, ...]


def _version_refs(record: DiscoveredRecord, official_ref: str) -> list[str]:
    """One official version reference per artifact. An artifact without a
    reference is the record itself — but only when it is the sole unlabelled
    artifact and no labelled artifact already claims the record's reference.
    Anything else would be a guess."""

    explicit = [
        a.official_version_ref.strip() if a.official_version_ref else None for a in record.artifacts
    ]
    missing = [i for i, ref in enumerate(explicit) if not ref]
    if len(missing) > 1 or (missing and official_ref in explicit):
        raise NormalizationError(
            f"{record.item_key}: several artifacts without official version references",
            ambiguous=True,
        )
    return [ref or official_ref for ref in explicit]


def normalize(record: DiscoveredRecord, *, expected_case_number: str) -> NormalizedDocument:
    """Map a discovered record onto Document / DocumentVersion fields.

    Raises NormalizationError when the case does not match, the official
    reference or title is missing, or versions cannot be told apart. Visibility
    is derived from the classification text and fails closed to UNKNOWN /
    NOT_PUBLIC; the pipeline never stores bytes for those.
    """

    if not CASE_NUMBER_RE.match(record.case_number):
        raise NormalizationError(f"{record.item_key}: malformed case number {record.case_number!r}")
    if record.case_number != expected_case_number:
        raise NormalizationError(
            f"{record.item_key}: record belongs to {record.case_number}, job is scoped to "
            f"{expected_case_number}"
        )
    official_ref = (record.official_ref or "").strip()
    if not official_ref:
        raise NormalizationError(f"{record.item_key}: official reference missing")
    if not official_ref.startswith(record.case_number):
        raise NormalizationError(
            f"{record.item_key}: official reference {official_ref!r} is not scoped to the case"
        )
    title = " ".join(record.title.split())
    if not title:
        raise NormalizationError(f"{record.item_key}: title missing")
    if not record.record_type.strip():
        raise NormalizationError(f"{record.item_key}: record type missing")

    record_visibility = visibility_from_classification(record.classification)

    versions: list[NormalizedVersion] = []
    seen_refs: set[str] = set()
    for artifact, ref in zip(record.artifacts, _version_refs(record, official_ref), strict=True):
        if ref in seen_refs:
            raise NormalizationError(
                f"{record.item_key}: duplicate version reference {ref!r}", ambiguous=True
            )
        seen_refs.add(ref)
        language = artifact.language or record.language
        vtype = artifact.version_type or classify_version_type(
            ref, title, artifact_language=language, record_language=record.language
        )
        if artifact.classification is not None:
            visibility = visibility_from_classification(artifact.classification)
        elif (
            record_visibility is Visibility.PUBLIC and vtype is DocumentVersionType.PUBLIC_REDACTED
        ):
            visibility = Visibility.PUBLIC_REDACTED
        else:
            visibility = record_visibility
        label = artifact.version_label
        if label is None and ref != official_ref and ref.startswith(official_ref + "/"):
            label = ref[len(official_ref) + 1 :]
        versions.append(
            NormalizedVersion(
                official_version_ref=ref,
                version_type=vtype,
                version_label=label,
                visibility=visibility,
                language=language,
                public_date=artifact.public_date or record.public_date,
                source_url=artifact.url,
                artifact=artifact,
            )
        )

    return NormalizedDocument(
        official_ref=official_ref,
        filing_number=filing_number(official_ref),
        title=title,
        document_type=record.record_type.strip().lower(),
        language=record.language,
        filing_party=record.filing_party or party_from_label(record.filing_party_label),
        document_date=record.document_date,
        filing_date=record.filing_date,
        public_date=record.public_date,
        visibility=record_visibility,
        versions=tuple(versions),
    )
