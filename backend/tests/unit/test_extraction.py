from unittest.mock import Mock

import pytest

from src.models.enums import Campus
from src.services import extraction
from src.services.extraction import (
    BlockKind,
    ExtractionError,
    extract_document,
    extract_html_document,
    extract_pdf_document,
)


def test_html_preserves_heading_list_dates_and_applicability() -> None:
    document = extract_html_document(
        """
        <main>
          <h1>Registration</h1>
          <h2>Fall term</h2>
          <p>Hammond students in Program: Biology must register by 2026-08-15 for Fall 2026.</p>
          <ul><li>Submit the form by September 1, 2026.</li></ul>
        </main>
        """
    )

    assert [block.kind for block in document.blocks] == [
        BlockKind.HEADING,
        BlockKind.HEADING,
        BlockKind.PARAGRAPH,
        BlockKind.LIST_ITEM,
    ]
    paragraph = document.blocks[2]
    assert paragraph.heading_path == ("Registration", "Fall term")
    assert paragraph.campus == Campus.HAMMOND
    assert paragraph.term == "Fall 2026"
    assert paragraph.program == "Biology"
    assert paragraph.dates[0].isoformat() == "2026-08-15"
    assert document.blocks[3].dates[0].isoformat() == "2026-09-01"


def test_table_rows_keep_header_labels_and_row_locators() -> None:
    document = extract_html_document(
        """
        <table>
          <caption>Academic schedule</caption>
          <thead><tr><th>Term</th><th>Deadline</th><th>Campus</th></tr></thead>
          <tbody><tr><td>Fall 2026</td><td>2026-08-15</td><td>Westville</td></tr></tbody>
        </table>
        """
    )

    row = next(block for block in document.blocks if block.kind == BlockKind.TABLE_ROW)
    assert row.text == "Term: Fall 2026 | Deadline: 2026-08-15 | Campus: Westville"
    assert row.locator == "Academic schedule, row 1"
    assert row.row == 1
    assert row.campus == Campus.WESTVILLE


def test_forms_preserve_labels_and_options_but_not_field_values() -> None:
    document = extract_html_document(
        """
        <form><h2>Term request</h2>
          <label for="term">Term</label>
          <select id="term" name="term"><option>Fall 2026</option></select>
          <label for="student">Student ID</label>
          <input id="student" name="student_id" value="123456" />
        </form>
        """
    )

    form = next(block for block in document.blocks if block.kind == BlockKind.FORM)
    assert "Term (select): Fall 2026" in form.text
    assert "Student ID (input)" in form.text
    assert "123456" not in form.text


def test_html_returns_discovered_links_without_fetching_them() -> None:
    document = extract_html_document(
        '<a href="../forms/appeal.pdf">Appeal form</a>'
        '<a href="javascript:alert(1)">Not a resource</a>',
        base_url="https://www.pnw.edu/registrar/",
    )

    assert len(document.links) == 1
    assert document.links[0].url == "https://www.pnw.edu/forms/appeal.pdf"
    assert document.links[0].title == "Appeal form"


def test_pdf_pages_preserve_page_locators_and_heading_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_page = Mock()
    first_page.extract_text.return_value = (
        "ACADEMIC CALENDAR\n\nHammond Fall 2026 begins 2026-08-15."
    )
    second_page = Mock()
    second_page.extract_text.return_value = "Westville Spring 2027 begins 2027-01-10."
    reader = Mock(pages=[first_page, second_page], is_encrypted=False)
    monkeypatch.setattr(extraction, "PdfReader", lambda *_args, **_kwargs: reader)

    document = extract_pdf_document(b"pdf-bytes")

    assert document.blocks[0].kind == BlockKind.HEADING
    assert document.blocks[1].heading_path == ("ACADEMIC CALENDAR",)
    assert document.blocks[1].locator == "Page 1"
    assert document.blocks[1].campus == Campus.HAMMOND
    assert document.blocks[1].term == "Fall 2026"
    assert document.blocks[2].locator == "Page 2"
    assert document.blocks[2].campus == Campus.WESTVILLE


def test_extract_document_rejects_unsupported_content_types() -> None:
    with pytest.raises(ExtractionError, match="unsupported content type"):
        extract_document(b"data", "application/octet-stream")


def test_pdf_parser_rejects_invalid_bytes() -> None:
    with pytest.raises(ExtractionError, match="unable to parse PDF"):
        extract_pdf_document(b"not a PDF")
