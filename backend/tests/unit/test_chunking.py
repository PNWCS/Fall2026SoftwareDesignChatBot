from datetime import date

import pytest

from src.models.enums import Campus
from src.services.chunking import CHUNKING_VERSION, chunk_document
from src.services.extraction import BlockKind, ExtractedBlock


def block(
    text: str,
    *,
    kind: BlockKind = BlockKind.PARAGRAPH,
    heading_path: tuple[str, ...] = ("Academic Schedule",),
    locator: str | None = None,
    dates: tuple[date, ...] = (),
    campus: Campus | None = None,
    term: str | None = None,
    program: str | None = None,
) -> ExtractedBlock:
    """Build a small extracted block so each test can focus on chunking behavior."""
    return ExtractedBlock(
        kind=kind,
        text=text,
        heading_path=heading_path,
        locator=locator,
        dates=dates,
        campus=campus,
        term=term,
        program=program,
    )


def test_chunking_is_deterministic_and_numbers_chunks_from_zero() -> None:
    blocks = [block("First paragraph."), block("Second paragraph.")]

    first_run = chunk_document(blocks)
    second_run = chunk_document(blocks)

    assert first_run == second_run
    assert len(first_run) == 1
    assert first_run[0].ordinal == 0
    assert first_run[0].chunking_version == CHUNKING_VERSION
    assert first_run[0].content == "First paragraph.\nSecond paragraph."


def test_chunks_keep_heading_and_applicability_metadata_separate() -> None:
    blocks = [
        block("Hammond Fall 2026 advising.", campus=Campus.HAMMOND, term="Fall 2026"),
        block("Westville Spring 2027 advising.", campus=Campus.WESTVILLE, term="Spring 2027"),
    ]

    chunks = chunk_document(blocks)

    assert [chunk.ordinal for chunk in chunks] == [0, 1]
    assert chunks[0].heading_path == "Academic Schedule"
    assert chunks[0].campus == Campus.HAMMOND
    assert chunks[0].term == "Fall 2026"
    assert chunks[1].campus == Campus.WESTVILLE
    assert chunks[1].term == "Spring 2027"


def test_table_rows_keep_individual_locators() -> None:
    blocks = [
        block("Date: August 24", kind=BlockKind.TABLE_ROW, locator="Table 1, row 1"),
        block("Date: September 7", kind=BlockKind.TABLE_ROW, locator="Table 1, row 2"),
    ]

    chunks = chunk_document(blocks)

    assert [chunk.content for chunk in chunks] == ["Date: August 24", "Date: September 7"]
    assert [chunk.locator for chunk in chunks] == ["Table 1, row 1", "Table 1, row 2"]


def test_long_blocks_split_within_limit_without_losing_words() -> None:
    text = "alpha beta gamma delta epsilon zeta eta theta"

    chunks = chunk_document([block(text)], max_chars=16)

    assert len(chunks) > 1
    assert all(len(chunk.content) <= 16 for chunk in chunks)
    assert " ".join(chunk.content for chunk in chunks) == text
    assert [chunk.ordinal for chunk in chunks] == list(range(len(chunks)))


def test_effective_date_range_requires_explicit_effective_language() -> None:
    chunks = chunk_document(
        [
            block(
                "Effective from 2026-01-01 through 2026-12-31.",
                dates=(date(2026, 1, 1), date(2026, 12, 31)),
            ),
            block("Deadline is 2026-08-24.", dates=(date(2026, 8, 24),)),
        ]
    )

    assert chunks[0].effective_from == date(2026, 1, 1)
    assert chunks[0].effective_to == date(2026, 12, 31)
    assert chunks[1].effective_from is None
    assert chunks[1].effective_to is None


@pytest.mark.parametrize(
    ("max_chars", "chunking_version"),
    [(0, CHUNKING_VERSION), (-1, CHUNKING_VERSION), (20, " ")],
)
def test_invalid_chunking_options_are_rejected(max_chars: int, chunking_version: str) -> None:
    with pytest.raises(ValueError):
        chunk_document([block("text")], max_chars=max_chars, chunking_version=chunking_version)
