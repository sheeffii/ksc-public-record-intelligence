from __future__ import annotations

from ksc_ingestion.pdf_parser import parse_pdf
from support.synthetic import make_pdf


def test_filing_parser_preserves_pdf_printed_page_and_numbered_paragraphs() -> None:
    parsed = parse_pdf(
        make_pdf(
            [
                "KSC-DEMO-0000/F00001/1 of 1",
                "I. PROCEDURAL BACKGROUND",
                "1. First paragraph cites F00002, para. 3.",
                "continued text",
                "2. Second paragraph.",
            ]
        ),
        transcript=False,
    )

    assert parsed.requires_review is False
    assert parsed.pages[0].pdf_page_index == 0
    assert parsed.pages[0].page_number == 1
    assert parsed.pages[0].printed_page_label == "1 of 1"
    assert [p.paragraph_number for p in parsed.paragraphs] == [1, 2]
    assert parsed.paragraphs[0].text.endswith("continued text")
    assert parsed.chunks[0].chunk_kind == "paragraph"
    assert parsed.sections[0].heading == "I. PROCEDURAL BACKGROUND"


def test_parser_never_fills_a_missing_printed_page_from_pdf_index() -> None:
    parsed = parse_pdf(
        make_pdf(["No printed source coordinate", "1. Source text."]), transcript=False
    )

    assert parsed.pages[0].pdf_page_index == 0
    assert parsed.pages[0].page_number is None
    assert parsed.requires_review is True
    assert "printed page not found" in parsed.review_reasons[0]


def test_transcript_parser_uses_only_printed_lines_and_withholds_closed_session_text() -> None:
    parsed = parse_pdf(
        make_pdf(
            [
                "KSC-OFFICIAL",
                "Page 100",
                " 1 [Open session]",
                " 2 PRESIDING JUDGE SMITH: Call the case.",
                " 3 Continue.",
                " 4 MR. DEMO: Response.",
                " 5 [Closed session]",
                " 6 not public",
                " 7 [Open session]",
                " 8 public again",
            ]
        ),
        transcript=True,
    )

    assert parsed.page_from == parsed.page_to == 100
    assert [(s.line_from, s.line_to) for s in parsed.transcript_segments] == [
        (1, 1),
        (2, 3),
        (4, 4),
        (5, 6),
        (7, 8),
    ]
    judge = parsed.transcript_segments[1]
    assert judge.speaker == "PRESIDING JUDGE SMITH"
    assert judge.speaker_role == "court"
    closed = parsed.transcript_segments[3]
    assert closed.closed_session is True
    assert closed.text == ""
