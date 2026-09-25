import pytest

from ksc_api.routers.records import _byte_range


def test_byte_ranges_are_bounded_to_the_exact_artifact() -> None:
    assert _byte_range(None, 100) is None
    assert _byte_range("bytes=10-19", 100) == (10, 19)
    assert _byte_range("bytes=90-", 100) == (90, 99)
    assert _byte_range("bytes=-10", 100) == (90, 99)
    assert _byte_range("bytes=90-200", 100) == (90, 99)


@pytest.mark.parametrize("value", ["items=0-1", "bytes=100-", "bytes=20-10", "bytes=0-1,4-5"])
def test_invalid_or_multi_ranges_fail_closed(value: str) -> None:
    with pytest.raises(ValueError):
        _byte_range(value, 100)
