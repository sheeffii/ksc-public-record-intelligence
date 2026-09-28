"""Parser v4 segmentation: text for page N stays on page N, ¶ numbers are
never invented, and one malformed paragraph never swallows the document."""

from __future__ import annotations

from ksc_ingestion.pdf_parser import (
    MAX_PARAGRAPH_PAGES,
    ParsedPage,
    _paragraphs_and_sections,
)

BODY = " " * 10
INDENT = " " * 15


def page(index: int, *lines: str) -> ParsedPage:
    return ParsedPage(
        pdf_page_index=index,
        page_number=index + 1,
        printed_page_label=str(index + 1),
        text="\n".join(
            [f"KSC-BC-2020-06/F00026/RED/{index + 1} of 236                 PUBLIC", *lines]
        ),
        running_head=None,
        has_redactions=False,
        redaction_extents=None,
    )


LONG = "the supporting material indicates a pattern of conduct over many months"


def test_wrapped_footnote_number_never_opens_a_paragraph() -> None:
    pages = [
        page(0, f"{BODY}1.  {LONG}", f"{BODY}{LONG} and further text here"),
        page(
            1,
            f"{BODY}{LONG}.12",
            f"{BODY}12 See infra paras 169, 271,",
            f"{BODY}359. [REDACTED]: infra",
        ),
        page(2, f"{BODY}2.  {LONG}", f"{BODY}{LONG} continues on this page"),
    ]
    paragraphs, _, _, _ = _paragraphs_and_sections(pages)
    assert [p.paragraph_number for p in paragraphs] == [1, 2]


def test_unreadable_paragraph_start_closes_the_open_paragraph() -> None:
    # ¶ numbers drawn as images: only the indented first line is visible.
    pages = [
        page(0, f"{BODY}1.  {LONG}", f"{BODY}{LONG} and it ends here."),
        page(1, f"{INDENT}In the present case, {LONG}", f"{BODY}{LONG} continues."),
    ]
    paragraphs, _, blocks, _ = _paragraphs_and_sections(pages)
    assert [(p.paragraph_number, p.pdf_page_index_to) for p in paragraphs] == [(1, 0)]
    page_two = [b for b in blocks if b.pdf_page_index == 1]
    assert [b.paragraph_number for b in page_two] == [None]
    assert page_two[0].text.startswith("In the present case")


def test_every_block_is_page_local_and_long_paragraphs_are_bounded() -> None:
    pages = [page(0, f"{BODY}1.  {LONG}")] + [
        page(i, f"{BODY}{LONG}", f"{BODY}{LONG}") for i in range(1, MAX_PARAGRAPH_PAGES + 4)
    ]
    paragraphs, _, blocks, reasons = _paragraphs_and_sections(pages)
    assert paragraphs[0].pdf_page_index_to - paragraphs[0].pdf_page_index_from < MAX_PARAGRAPH_PAGES
    assert reasons and "would exceed" in reasons[0]
    assert all(b.text for b in blocks)
    assert {b.pdf_page_index for b in blocks} == set(range(len(pages)))


def test_footnotes_are_separated_and_dates_are_not_footnotes() -> None:
    pages = [
        page(
            0,
            f"{BODY}1.  The Defence cases commenced on 15 September 2025,10 and closed",
            f"{BODY}15 September was the date of the first hearing in this matter today",
            f"{BODY}10 F02964, Decision on Defence Motion, para. 4.",
        )
    ]
    paragraphs, _, blocks, _ = _paragraphs_and_sections(pages)
    assert "15 September was the date" in paragraphs[0].text
    assert "F02964" not in paragraphs[0].text
    assert [b.kind for b in blocks] == ["paragraph", "footnotes"]
    assert blocks[1].text.startswith("10 F02964")


def test_numbered_heading_is_a_section_not_a_paragraph() -> None:
    pages = [
        page(
            0,
            f"{BODY}4.  Counts 8 and 9: Murder",
            f"{INDENT}The supporting material shows {LONG}",
            f"{BODY}{LONG} and ends.",
            f"{BODY}5.  {LONG}",
            f"{BODY}{LONG}.",
        )
    ]
    paragraphs, sections, _, _ = _paragraphs_and_sections(pages)
    assert [p.paragraph_number for p in paragraphs] == [5]
    assert any(s.heading == "4. Counts 8 and 9: Murder" for s in sections)
