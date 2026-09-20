from __future__ import annotations

from ksc_api.models import CitationType
from ksc_ingestion.citation_resolution import canonical_identifier, extract_citations


def test_citation_extraction_preserves_raw_text_and_normalizes_exact_identifiers() -> None:
    text = "See KSC-BC-2020-06/F00004/RED, para. 3 and F03776, p. 2; W01234; P00123."
    citations = extract_citations(text)

    assert [c.normalized_identifier for c in citations] == [
        "KSC-BC-2020-06/F00004/RED",
        "F03776",
        "W01234",
        "P00123",
    ]
    assert citations[0].raw_text == "KSC-BC-2020-06/F00004/RED, para. 3"
    assert citations[0].citation_type == CitationType.PARAGRAPH
    assert citations[0].target_para_from == citations[0].target_para_to == 3
    assert citations[1].citation_type == CitationType.PAGE
    assert citations[1].target_page == 2
    assert citations[2].citation_type == CitationType.WITNESS
    assert citations[3].citation_type == CitationType.EXHIBIT
    assert text[citations[0].source_start : citations[0].source_end] == citations[0].raw_text


def test_transcript_page_and_line_reference_is_not_invented() -> None:
    citation = extract_citations("Transcript page 29,148, lines 6-9")[0]

    assert citation.normalized_identifier == "T.29148"
    assert citation.citation_type == CitationType.TRANSCRIPT_LINE
    assert citation.target_page == 29148
    assert (citation.target_line_from, citation.target_line_to) == (6, 9)


def test_compact_version_suffixes_normalize_without_fuzzy_matching() -> None:
    assert canonical_identifier("IA042-F00005RED") == "IA042/F00005/RED"
    assert canonical_identifier("F03667CORRED") == "F03667/COR/RED"
    assert canonical_identifier("F03664RED2") == "F03664/RED2"


def test_plausible_but_unrecognized_text_is_not_extracted_as_a_citation() -> None:
    assert extract_citations("F123 is not a valid filing; witness W12 is not a valid code") == []
