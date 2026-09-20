from __future__ import annotations

import pytest

from ksc_ingestion.artifacts import UnsupportedArtifactError, inspect, sha256_hex, sniff_mime
from ksc_ingestion.storage import InMemoryObjectStore, storage_key
from support.synthetic import make_pdf


def test_inspect_pdf_reports_hash_size_pages_and_case_numbers() -> None:
    data = make_pdf(["KSC-DEMO-0000/F00001", "hello"])
    info = inspect(data)
    assert info.sha256 == sha256_hex(data)
    assert info.byte_size == len(data)
    assert info.mime_type == "application/pdf"
    assert info.page_count == 1
    assert info.case_numbers_on_first_page == ("KSC-DEMO-0000",)
    assert info.has_text_layer is True


def test_identical_bytes_identical_hash_and_different_text_different_hash() -> None:
    assert sha256_hex(make_pdf(["a"])) == sha256_hex(make_pdf(["a"]))
    assert sha256_hex(make_pdf(["a"])) != sha256_hex(make_pdf(["b"]))


@pytest.mark.parametrize(
    "data", [b"", b"<html>error</html>", b"PDF-1.4 no magic", b"%PDF-1.4 but truncated"]
)
def test_non_pdf_bytes_are_unsupported(data: bytes) -> None:
    assert sniff_mime(data) in (None, "application/pdf")
    with pytest.raises(UnsupportedArtifactError):
        inspect(data)


def test_storage_key_is_hash_addressed_and_safe() -> None:
    key = storage_key("KSC-DEMO-0000", "KSC-DEMO-0000/F00001/RED", "ab" * 32)
    assert key == f"documents/KSC-DEMO-0000/KSC-DEMO-0000_F00001_RED/{'ab' * 32}.pdf"
    assert "/../" not in storage_key("KSC-DEMO-0000", "../x y", "0" * 64)


def test_in_memory_store_never_overwrites() -> None:
    store = InMemoryObjectStore()
    store.put("k", b"first", "application/pdf")
    store.put("k", b"second", "application/pdf")
    assert store.exists("k")
    assert store.objects["k"] == b"first"
    assert store.get("k") == b"first"
