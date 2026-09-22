"""Deterministic, conservative metadata normalization."""

from __future__ import annotations

from datetime import date

import pytest

from ksc_api.models.enums import DocumentVersionType, Party, SourceSystem, Visibility
from ksc_ingestion.discovery import (
    DiscoveredArtifact,
    DiscoveredRecord,
    MetadataSource,
    visibility_from_classification,
)
from ksc_ingestion.normalize import (
    NormalizationError,
    classify_version_type,
    date_in_text,
    filing_number,
    normalize,
    parse_date,
    party_from_label,
)

CASE = "KSC-DEMO-0000"
PCR = "https://repository.scp-ks.org"


def record(**overrides: object) -> DiscoveredRecord:
    base: dict[str, object] = {
        "source_system": SourceSystem.KSC_PUBLIC_COURT_RECORDS,
        "external_record_id": "00000000000000a1",
        "record_type": "Filing",
        "case_number": CASE,
        "title": "  Synthetic   filing ",
        "discovery_url": f"{PCR}/?icc_filters[case_number]={CASE}",
        "detail_page_url": f"{PCR}/details.php?doc_id=00000000000000a1&doc_type=stl_filing&lang=eng",
        "metadata_source": MetadataSource.SYNTHETIC_FIXTURE,
        "official_ref": f"{CASE}/F00001",
        "language": "en",
        "classification": "Public",
        "artifacts": (DiscoveredArtifact(url=f"{PCR}/LW/Published/Filing/x/F00001.pdf"),),
    }
    base.update(overrides)
    return DiscoveredRecord(**base)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2024-11-25", date(2024, 11, 25)),
        ("2024-11-25T10:00:00", date(2024, 11, 25)),
        ("25 November 2024", date(2024, 11, 25)),
        ("Trial Hearing - 25 November 2024 - Public Redacted", date(2024, 11, 25)),
        ("25/11/2024", date(2024, 11, 25)),
        ("31 February 2024", None),
        ("November 2024", None),
        ("", None),
        (None, None),
        (date(2020, 1, 1), date(2020, 1, 1)),
    ],
)
def test_parse_date(raw: object, expected: date | None) -> None:
    assert parse_date(raw) == expected  # type: ignore[arg-type]


def test_date_in_text() -> None:
    assert date_in_text("Trial Hearing - 3 April 2023") == date(2023, 4, 3)
    assert date_in_text("no date here") is None


@pytest.mark.parametrize(
    ("ref", "expected"),
    [
        ("KSC-BC-2020-06/F00005", "F00005"),
        ("KSC-BC-2020-06/F00005/RED", "F00005"),
        ("KSC-BC-2020-06/F01234/A01", "F01234"),
        ("KSC-BC-2020-06/IA002/F00001", None),
        ("F00005", None),
        (None, None),
    ],
)
def test_filing_number(ref: str | None, expected: str | None) -> None:
    assert filing_number(ref) == expected


@pytest.mark.parametrize(
    ("classification", "expected"),
    [
        ("Public", Visibility.PUBLIC),
        ("PUBLIC", Visibility.PUBLIC),
        ("Public Redacted", Visibility.PUBLIC_REDACTED),
        ("Confidential", Visibility.NOT_PUBLIC),
        ("Strictly Confidential and Ex Parte", Visibility.NOT_PUBLIC),
        ("Confidential with public annex", Visibility.NOT_PUBLIC),
        ("Under seal", Visibility.NOT_PUBLIC),
        ("", Visibility.UNKNOWN),
        (None, Visibility.UNKNOWN),
        ("something else", Visibility.UNKNOWN),
    ],
)
def test_visibility_fails_closed(classification: str | None, expected: Visibility) -> None:
    assert visibility_from_classification(classification) is expected


@pytest.mark.parametrize(
    ("ref", "title", "langs", "expected"),
    [
        ("KSC-BC-2020-06/F00005/RED", "x", ("en", "en"), DocumentVersionType.PUBLIC_REDACTED),
        ("KSC-BC-2020-06/F00005-RED", "x", ("en", "en"), DocumentVersionType.PUBLIC_REDACTED),
        (
            "KSC-BC-2020-06/F00005",
            "Public Redacted Version of X",
            ("en", "en"),
            DocumentVersionType.PUBLIC_REDACTED,
        ),
        ("KSC-BC-2020-06/F00005/COR", "x", ("en", "en"), DocumentVersionType.CORRECTED),
        (
            "KSC-BC-2020-06/F00005",
            "Corrected Version of X",
            ("en", "en"),
            DocumentVersionType.CORRECTED,
        ),
        ("KSC-BC-2020-06/F00005/RED/COR", "x", ("en", "en"), DocumentVersionType.PUBLIC_REDACTED),
        (
            "KSC-BC-2020-06/F00005",
            "Reclassified as public",
            ("en", "en"),
            DocumentVersionType.RECLASSIFIED,
        ),
        ("KSC-BC-2020-06/F00005/ALB", "x", ("sq", "en"), DocumentVersionType.TRANSLATION),
        ("KSC-BC-2020-06/F00005", "x", ("en", "en"), DocumentVersionType.ORIGINAL),
        (
            "KSC-BC-2020-06/F00005",
            "Request to CORE team",
            ("en", "en"),
            DocumentVersionType.ORIGINAL,
        ),
    ],
)
def test_classify_version_type(
    ref: str, title: str, langs: tuple[str, str], expected: DocumentVersionType
) -> None:
    assert (
        classify_version_type(ref, title, artifact_language=langs[0], record_language=langs[1])
        is expected
    )


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("Specialist Prosecutor", Party.SPO),
        ("Thaçi Defence", Party.DEFENCE),
        ("Victims' Counsel", Party.VICTIMS_COUNSEL),
        ("Trial Panel II", Party.COURT),
        ("Pre-Trial Judge", Party.COURT),
        ("Registry", Party.OTHER),
        ("", None),
        (None, None),
    ],
)
def test_party_from_label(label: str | None, expected: Party | None) -> None:
    assert party_from_label(label) is expected


def test_normalize_single_artifact_is_the_record_itself() -> None:
    doc = normalize(record(), expected_case_number=CASE)
    assert doc.official_ref == f"{CASE}/F00001"
    assert doc.filing_number == "F00001"
    assert doc.title == "Synthetic filing"
    assert doc.document_type == "filing"
    assert doc.visibility is Visibility.PUBLIC
    (version,) = doc.versions
    assert version.official_version_ref == f"{CASE}/F00001"
    assert version.version_type is DocumentVersionType.ORIGINAL
    assert version.visibility is Visibility.PUBLIC
    assert version.version_label is None


def test_normalize_redacted_version_inherits_public_redacted_visibility() -> None:
    art = DiscoveredArtifact(
        url=f"{PCR}/LW/Published/Filing/x/F00001-RED.pdf",
        official_version_ref=f"{CASE}/F00001/RED",
    )
    doc = normalize(record(artifacts=(art,)), expected_case_number=CASE)
    (version,) = doc.versions
    assert version.version_type is DocumentVersionType.PUBLIC_REDACTED
    assert version.visibility is Visibility.PUBLIC_REDACTED
    assert version.version_label == "RED"


def test_normalize_keeps_dates_separate_and_never_infers() -> None:
    doc = normalize(
        record(filing_date=date(2020, 5, 28), filing_party_label="Specialist Prosecutor"),
        expected_case_number=CASE,
    )
    assert doc.filing_date == date(2020, 5, 28)
    assert doc.document_date is None
    assert doc.public_date is None
    assert doc.filing_party is Party.SPO


def test_normalize_unknown_classification_is_not_public() -> None:
    doc = normalize(record(classification=None), expected_case_number=CASE)
    assert doc.visibility is Visibility.UNKNOWN
    assert doc.versions[0].visibility is Visibility.UNKNOWN


@pytest.mark.parametrize(
    ("overrides", "ambiguous", "match"),
    [
        ({"case_number": "KSC-BC-2020-06"}, False, "scoped to"),
        ({"case_number": "nonsense"}, False, "malformed"),
        ({"official_ref": None}, False, "official reference missing"),
        ({"official_ref": "KSC-BC-2020-06/F00001"}, False, "not scoped to the case"),
        ({"title": "   "}, False, "title missing"),
        ({"record_type": ""}, False, "record type missing"),
        (
            {
                "artifacts": (
                    DiscoveredArtifact(url=f"{PCR}/LW/Published/Filing/x/a.pdf"),
                    DiscoveredArtifact(url=f"{PCR}/LW/Published/Filing/x/b.pdf"),
                )
            },
            True,
            "several artifacts",
        ),
        (
            {
                "artifacts": (
                    DiscoveredArtifact(
                        url=f"{PCR}/LW/Published/Filing/x/a.pdf",
                        official_version_ref=f"{CASE}/F00001",
                    ),
                    DiscoveredArtifact(
                        url=f"{PCR}/LW/Published/Filing/x/b.pdf",
                        official_version_ref=f"{CASE}/F00001",
                    ),
                )
            },
            True,
            "duplicate version reference",
        ),
    ],
)
def test_normalize_refuses_to_guess(
    overrides: dict[str, object], ambiguous: bool, match: str
) -> None:
    with pytest.raises(NormalizationError, match=match) as exc:
        normalize(record(**overrides), expected_case_number=CASE)
    assert exc.value.ambiguous is ambiguous


def test_importer_ambiguous_reference_is_never_the_record_itself() -> None:
    """A capture the importer marked ambiguous (PDF header contradicts the
    published id) must not fall back to the sole-unlabelled-artifact default."""
    raw = {
        "metadata": {
            "extra": {
                "reference": {
                    "status": "ambiguous",
                    "source": "conflict",
                    "note": "pdf header 'X/F03734' contradicts published id 'F03734RED'",
                }
            }
        }
    }
    with pytest.raises(NormalizationError, match="version reference ambiguous") as exc:
        normalize(record(raw_metadata=raw), expected_case_number=CASE)
    assert exc.value.ambiguous is True
    # The same record with a confirmed reference normalises as before.
    raw["metadata"]["extra"]["reference"]["status"] = "ok"
    assert normalize(record(raw_metadata=raw), expected_case_number=CASE).versions
