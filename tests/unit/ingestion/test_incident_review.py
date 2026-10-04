"""The first reviewed incident batch writes only cleared SPO allegations."""

from __future__ import annotations

import pytest

from ksc_ingestion import incident_review as review


def test_only_cleared_candidates_are_written() -> None:
    written = {candidate.key for candidate in review._CANDIDATES}

    assert written == {
        "INC-CAND-01",
        "INC-CAND-02",
        "INC-CAND-04",
        "INC-CAND-05",
        "INC-CAND-06",
        "INC-CAND-07",
    }
    assert written.isdisjoint(review.HELD_CANDIDATES)
    assert review.HELD_CANDIDATES == {
        "INC-CAND-03": "POSSIBLY_AFFECTED",
        "INC-CAND-08": "CANNOT_DETERMINE",
    }


def test_bare_and_bajgore_share_their_source_paragraphs() -> None:
    by_key = {candidate.key: candidate for candidate in review._CANDIDATES}
    bare, bajgore = by_key["INC-CAND-04"], by_key["INC-CAND-05"]

    assert bare.operative == bajgore.operative
    assert bare.shares_source_with == "INC-CAND-05"
    assert bajgore.shares_source_with == "INC-CAND-04"


def test_every_place_has_a_held_municipality_and_no_coordinates() -> None:
    slugs = {place.slug for place in review._PLACES}

    for place in review._PLACES:
        assert place.kind in {"village", "municipality"}
        assert (place.parent is None) == (place.kind == "municipality")
        assert place.parent is None or place.parent in slugs
    assert {candidate.place for candidate in review._CANDIDATES} <= slugs


def test_trailing_heading_is_removed_exactly() -> None:
    text = "Detainees were held. Llapushnik/Lapušnik"

    assert review.operative_excerpt(text, "Llapushnik/Lapušnik") == "Detainees were held."
    assert review.operative_excerpt(text, None) == text


def test_missing_trailing_heading_fails_closed() -> None:
    with pytest.raises(RuntimeError):
        review.operative_excerpt("Detainees were held.", "Drenoc/Drenovac")


def test_disjoint_periods_keep_only_the_pleaded_wording() -> None:
    zllash = next(c for c in review._CANDIDATES if c.key == "INC-CAND-07")

    assert zllash.date_from is None and zllash.date_to is None
    assert zllash.date_as_pleaded.startswith("In September 1998 and between")
