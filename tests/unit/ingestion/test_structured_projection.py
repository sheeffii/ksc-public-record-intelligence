from ksc_ingestion.structured_projection import _person_identity, _status


def test_public_speaker_identity_is_deterministic_across_language_labels() -> None:
    assert _person_identity("JUDGE GUILLOU") == ("judge-guillou", "Judge Guillou", "judge")
    assert _person_identity("GJYKATËSI GUILLOU") == (
        "judge-guillou",
        "Judge Guillou",
        "judge",
    )
    assert _person_identity("THE WITNESS") is None


def test_exhibit_status_requires_explicit_nearby_language() -> None:
    assert _status("The corrected statement was admitted as P01136.", "P01136") == "admitted"
    assert _status("The party referred to P01136 in submissions.", "P01136") == "unknown"
