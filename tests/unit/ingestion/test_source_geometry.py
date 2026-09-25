import io

from pypdf import PdfReader, PdfWriter

from ksc_api.models import PageTextGeometry, TextExtractionMethod
from ksc_ingestion.source_geometry import _matches, extract_native_geometry
from support.synthetic import make_pdf


def test_native_geometry_preserves_page_dimensions_text_and_boxes() -> None:
    pages = extract_native_geometry(make_pdf(["KSC-DEMO-0000/F00001", "Exact source words"]))

    assert len(pages) == 1
    page = pages[0]
    assert (page.width, page.height, page.rotation) == (612.0, 792.0, 0)
    assert "Exact source words" in page.text
    exact = [word for word in page.words if word.text in {"Exact", "source", "words"}]
    assert [word.text for word in exact] == ["Exact", "source", "words"]
    assert all(word.width > 0 and word.height > 0 and word.x >= 0 and word.y >= 0 for word in exact)


def test_geometry_match_requires_one_exact_token_sequence() -> None:
    words = [
        PageTextGeometry(
            text=text,
            sequence=index,
            document_version_id=None,  # type: ignore[arg-type]
            pdf_page_index=0,
            char_start=index * 2,
            char_end=index * 2 + 1,
            x=index * 10,
            y=10,
            width=8,
            height=10,
            extraction_method=TextExtractionMethod.NATIVE_TEXT,
            extraction_state="usable",
        )
        for index, text in enumerate(["W01234", "said", "W01234"])
    ]
    assert len(_matches(words, "W01234")) == 2
    assert [[word.text for word in match] for match in _matches(words, "W01234 said")] == [
        ["W01234", "said"]
    ]


def test_rotated_page_keeps_valid_version_specific_coordinates() -> None:
    reader = PdfReader(io.BytesIO(make_pdf(["Rotated exact text"])))
    writer = PdfWriter()
    writer.add_page(reader.pages[0].rotate(90))
    output = io.BytesIO()
    writer.write(output)

    page = extract_native_geometry(output.getvalue())[0]
    assert page.rotation == 90
    assert all(
        0 <= word.x < page.width
        and 0 <= word.y < page.height
        and word.x + word.width <= page.width
        and word.y + word.height <= page.height
        for word in page.words
    )
