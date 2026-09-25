from dataclasses import dataclass

from ksc_ingestion.transcript_sync import line_grid, segment_regions


@dataclass(frozen=True)
class W:
    text: str
    x: float
    y: float
    width: float = 20.0
    height: float = 10.0


def _page(lines: dict[int, str], *, extra: list[W] | None = None) -> list[W]:
    """A transcript page: right-aligned line numbers, body text at x=108."""
    words: list[W] = [W("Witness:", 36, 40), W("W03877", 90, 40)]
    for number, body in lines.items():
        top = 90 + (number - 1) * 25
        label = str(number)
        words.append(W(label, 45 - 7 * len(label), top, 7 * len(label)))
        x = 108.0
        for token in body.split():
            words.append(W(token, x, top - 1, 6 * len(token), 12))
            x += 6 * len(token) + 5
    return words + (extra or [])


def _regions(words: list[W], **segment: object):
    grid, reason = line_grid(words)
    return segment_regions(grid, reason, page_width=599, page_height=847, **segment)  # type: ignore[arg-type]


def test_exact_segment_gets_one_box_per_line_and_excludes_header_and_numbers() -> None:
    words = _page({1: "THE WITNESS: Conscious of", 2: "the significance.", 3: "JUDGE: Next."})
    boxes, reason = _regions(
        words, speaker="THE WITNESS", text="Conscious of the significance.", line_from=1, line_to=2
    )
    assert reason is None
    assert [box.number for box in boxes] == [1, 2]
    assert boxes[0].text == "THE WITNESS: Conscious of"
    assert all(box.x >= 108 for box in boxes)  # never the line-number column


def test_text_mismatch_is_refused_rather_than_boxed() -> None:
    words = _page({1: "THE WITNESS: Conscious of", 2: "the significance."})
    boxes, reason = _regions(
        words, speaker="THE WITNESS", text="Conscious of a different text.", line_from=1, line_to=2
    )
    assert boxes == [] and reason == "geometry_line_text_mismatch"


def test_missing_line_number_column_or_line_is_explicit() -> None:
    no_grid = [W("THE", 108, 90), W("WITNESS:", 140, 90)]
    boxes, reason = _regions(no_grid, speaker=None, text="THE WITNESS:", line_from=1, line_to=1)
    assert boxes == [] and reason == "geometry_line_grid_not_found"
    words = _page({1: "One.", 2: "Two."})
    boxes, reason = _regions(words, speaker=None, text="Three.", line_from=3, line_to=3)
    assert boxes == [] and reason == "geometry_line_missing"


def test_two_candidate_number_columns_are_ambiguous() -> None:
    words = _page({1: "One.", 2: "Two."})
    # A second right-aligned 1..2 column far to the right (e.g. a table).
    words += [W("1", 500, 90, 7), W("2", 500, 115, 7)]
    grid, reason = line_grid(words)
    assert grid is None and reason == "geometry_line_grid_ambiguous"


def test_non_sequential_numbers_do_not_form_a_grid() -> None:
    words = [W("1", 38, 90, 7), W("3", 38, 115, 7), W("text", 108, 90)]
    grid, reason = line_grid(words)
    assert grid is None and reason == "geometry_line_grid_not_found"
