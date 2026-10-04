"""A numbered paragraph that runs onto the next page keeps its continuation,
even when that page's header carries a bare filing timestamp; a new numbered
paragraph or a section heading on the next page still starts fresh."""

from __future__ import annotations

from ksc_ingestion.pdf_parser import ParsedPage, _paragraphs_and_sections

_HEADER = [
    "KSC-BC-2020-06/F00999/A03/{n} of 68                                         PUBLIC",
    "                                                              30/09/2022 11:42:00",
]
_LINE = "       Multiple KLA members routinely subjected detainees to severe beatings and abuse."


def _page(index: int, body: list[str]) -> ParsedPage:
    lines = [line.format(n=index + 1) for line in _HEADER] + body
    return ParsedPage(index, index + 1, None, "\n".join(lines), None, False, None)


def _first_page() -> ParsedPage:
    return _page(
        0, ["       1.    Detainees were held in a cowshed. " + _LINE.strip(), _LINE, _LINE]
    )


def test_paragraph_continues_across_a_page_break() -> None:
    pages = [
        _first_page(),
        _page(1, ["       kicked. Detainees could hear the abuse of others.", _LINE]),
    ]

    paragraphs, _, _, _ = _paragraphs_and_sections(pages)

    assert [p.paragraph_number for p in paragraphs] == [1]
    (only,) = paragraphs
    assert (only.pdf_page_index_from, only.pdf_page_index_to) == (0, 1)
    assert (only.page_from, only.page_to) == (1, 2)
    assert "kicked. Detainees could hear the abuse of others." in only.text
    assert "30/09/2022" not in only.text


def test_new_numbered_paragraph_on_the_next_page_stays_separate() -> None:
    pages = [
        _first_page(),
        _page(1, ["       2.    The detainees were later released. " + _LINE.strip(), _LINE]),
    ]

    paragraphs, _, _, _ = _paragraphs_and_sections(pages)

    assert [p.paragraph_number for p in paragraphs] == [1, 2]
    assert paragraphs[0].pdf_page_index_to == 0
    assert paragraphs[1].pdf_page_index_from == 1


def test_section_heading_on_the_next_page_is_not_merged() -> None:
    pages = [
        _first_page(),
        _page(1, ["II. APPLICABLE LAW", "       2.    The law provides. " + _LINE.strip(), _LINE]),
    ]

    paragraphs, sections, _, _ = _paragraphs_and_sections(pages)

    assert [p.paragraph_number for p in paragraphs] == [1, 2]
    assert "APPLICABLE LAW" not in paragraphs[0].text
    assert any(section.heading == "II. APPLICABLE LAW" for section in sections)


def test_segmentation_is_idempotent() -> None:
    pages = [
        _first_page(),
        _page(1, ["       kicked. Detainees could hear the abuse of others.", _LINE]),
    ]

    assert _paragraphs_and_sections(pages) == _paragraphs_and_sections(pages)
