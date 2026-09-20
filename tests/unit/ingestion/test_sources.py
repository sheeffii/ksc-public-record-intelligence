"""Official host allowlist and URL classification."""

from __future__ import annotations

import pytest

from ksc_api.models.enums import SourceSystem
from ksc_ingestion.sources import (
    NotOfficialSourceError,
    UrlKind,
    canonicalize,
    classify,
    is_official,
    normalize_language,
    require_official,
)

DETAIL = (
    "https://repository.scp-ks.org/details.php?doc_id=091ec6e98038f36c&doc_type=stl_filing&lang=eng"
)
DETAIL_JUNK = (
    "https://repository.scp-ks.org/details.php?doc_id=091EC6E98038F36C&amp=&doc_type=stl_filing"
    "&amp=&lang=eng"
)
LISTING = (
    "https://repository.scp-ks.org/?icc_filters%5Bcase_number%5D=KSC-BC-2020-06"
    "&icc_filters%5Blanguage_short%5D=_all&icc_filters%5Brecord_type_short%5D=_all"
    "&icc_filters%5Bsort_order%5D=_sort_date_newest/1000&page=211"
)
FILING_PDF = "https://repository.scp-ks.org/LW/Published/Filing/0b1ec6e9811e07df/Some%20Title.pdf"
TRANSCRIPT_PDF = (
    "https://repository.scp-ks.org/LW/Published/Transcript/KSC-BC-2020-06/"
    "Trial%20Hearing%20-%2025%20November%202024%20-%20Public%20Redacted.pdf"
)


@pytest.mark.parametrize(
    "url",
    [
        "http://repository.scp-ks.org/details.php?doc_id=091ec6e98038f36c",
        "https://example.com/details.php?doc_id=091ec6e98038f36c",
        "https://scp-ks.org.evil.example/",
        "https://web.archive.org/web/2024/https://repository.scp-ks.org/",
        "ftp://repository.scp-ks.org/x.pdf",
        "",
    ],
)
def test_non_official_urls_are_refused(url: str) -> None:
    assert not is_official(url)
    with pytest.raises(NotOfficialSourceError):
        require_official(url)
    with pytest.raises(NotOfficialSourceError):
        classify(url)


def test_detail_page_classification() -> None:
    c = classify(DETAIL)
    assert c.kind is UrlKind.PCR_DETAIL
    assert c.source_system is SourceSystem.KSC_PUBLIC_COURT_RECORDS
    assert (c.doc_id, c.doc_type, c.lang) == ("091ec6e98038f36c", "stl_filing", "eng")


def test_canonicalize_strips_search_engine_junk_and_orders_parameters() -> None:
    assert canonicalize(DETAIL_JUNK) == DETAIL
    assert canonicalize(DETAIL) == DETAIL


def test_malformed_doc_id_is_refused() -> None:
    with pytest.raises(NotOfficialSourceError):
        classify("https://repository.scp-ks.org/details.php?doc_id=../etc&doc_type=stl_filing")


def test_listing_classification() -> None:
    c = classify(LISTING)
    assert c.kind is UrlKind.PCR_LISTING
    assert c.page == 211
    assert dict(c.filters)["case_number"] == "KSC-BC-2020-06"
    assert dict(c.filters)["record_type_short"] == "_all"


def test_artifact_classification_and_canonical_form_is_untouched() -> None:
    filing = classify(FILING_PDF)
    transcript = classify(TRANSCRIPT_PDF)
    assert (filing.kind, filing.artifact_kind) == (UrlKind.PCR_ARTIFACT, "Filing")
    assert (transcript.kind, transcript.artifact_kind) == (UrlKind.PCR_ARTIFACT, "Transcript")
    assert canonicalize(TRANSCRIPT_PDF) == TRANSCRIPT_PDF


def test_case_site_and_other_official_pages() -> None:
    case_page = classify("https://www.scp-ks.org/en/cases/ksc-bc-2020-06")
    assert case_page.kind is UrlKind.CASE_PAGE
    assert case_page.source_system is SourceSystem.KSC_CASE_PAGE
    other = classify("https://repository.scp-ks.org/help")
    assert other.kind is UrlKind.OTHER_OFFICIAL
    assert other.source_system is SourceSystem.OTHER_OFFICIAL_KSC


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("eng", "en"),
        ("ENG", "en"),
        ("alb", "sq"),
        ("srb", "sr"),
        ("_all", None),
        (None, None),
        ("xx", "xx"),
    ],
)
def test_language_normalization_never_guesses(raw: str | None, expected: str | None) -> None:
    assert normalize_language(raw) == expected
