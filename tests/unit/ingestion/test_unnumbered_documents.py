"""A long document whose few "numbered paragraphs" are really headings or
contents entries is treated as not paragraph-numbered; numbered documents
and short documents are unaffected."""

from __future__ import annotations

from ksc_ingestion.pdf_parser import ParsedPage, _paragraphs_and_sections

_PROSE = (
    "The record shows that the events described here were reported in several public "
    "sources and the Panel considered them together with the remaining evidence.12"
)


def _page(index: int, lines: list[str]) -> ParsedPage:
    return ParsedPage(index, index + 1, None, "\n".join(lines), None, False, None)


def test_long_document_with_stray_numbered_headings_keeps_no_paragraph_numbers() -> None:
    # Like the 716-page SPO Final Trial Brief: numbered headings only, each of
    # which would otherwise open a paragraph that runs on for several pages.
    pages = [_page(i, [_PROSE, _PROSE]) for i in range(300)]
    pages[3] = _page(3, ["1. Emergence of the Common Plan", _PROSE])
    pages[60] = _page(60, ["2. Plurality of Persons", _PROSE])

    paragraphs, _, blocks, reasons = _paragraphs_and_sections(pages)

    assert paragraphs == []
    assert all(block.paragraph_number is None for block in blocks)
    # Not a parse defect, so no review reason (the false paragraphs' notes go too).
    assert reasons == []
    # The text itself is never dropped.
    assert any("Emergence of the Common Plan" in block.text for block in blocks)


def test_long_paragraph_numbered_document_keeps_its_numbers() -> None:
    pages = [_page(i, [f"{i + 1}. {_PROSE}", _PROSE]) for i in range(120)]

    paragraphs, _, _, reasons = _paragraphs_and_sections(pages)

    assert [p.paragraph_number for p in paragraphs] == list(range(1, 121))
    assert reasons == []


def test_short_document_is_never_treated_as_unnumbered() -> None:
    pages = [_page(i, [_PROSE]) for i in range(40)]
    pages[0] = _page(0, [f"1. {_PROSE}"])

    paragraphs, _, _, _ = _paragraphs_and_sections(pages)

    assert [p.paragraph_number for p in paragraphs] == [1]
