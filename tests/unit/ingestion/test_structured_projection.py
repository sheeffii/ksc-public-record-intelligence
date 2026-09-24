from ksc_ingestion.structured_projection import _person_identity


def test_public_speaker_identity_is_deterministic_across_language_labels() -> None:
    assert _person_identity("JUDGE GUILLOU") == ("judge-guillou", "Judge Guillou", "judge")
    assert _person_identity("GJYKATËSI GUILLOU") == (
        "judge-guillou",
        "Judge Guillou",
        "judge",
    )
    assert _person_identity("THE WITNESS") is None
