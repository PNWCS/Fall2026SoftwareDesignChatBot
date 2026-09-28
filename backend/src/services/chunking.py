import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from src.models.enums import Campus
from src.services.extraction import BlockKind, ExtractedBlock

# This name is stored with chunks so a later ingestion can identify the rules used.
CHUNKING_VERSION = "structure-v1"
# Character limits keep a chunk small enough for retrieval while avoiding tokenizer-specific code.
DEFAULT_MAX_CHARS = 1200
# These words indicate that two dates describe the start and end of an effective period.
_EFFECTIVE_RANGE_MARKER = re.compile(r"\b(?:through|until|to)\b", re.IGNORECASE)


@dataclass(frozen=True)
class Chunk:
    """One retrieval-sized piece of source text and its provenance metadata.

    ``ordinal`` is the stable, zero-based position within the chunked document.
    Applicability and locator fields are copied from the source blocks so later
    retrieval can filter or cite the chunk without re-parsing its text.
    """

    ordinal: int
    content: str
    chunking_version: str
    heading_path: str | None
    locator: str | None
    campus: Campus | None
    term: str | None
    program: str | None
    effective_from: date | None
    effective_to: date | None


@dataclass(frozen=True)
class _ChunkContext:
    """Metadata that must remain the same for every block in one chunk."""

    heading_path: str | None
    locator: str | None
    campus: Campus | None
    term: str | None
    program: str | None
    effective_from: date | None
    effective_to: date | None


def chunk_document(
    blocks: Iterable[ExtractedBlock],
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
    chunking_version: str = CHUNKING_VERSION,
) -> tuple[Chunk, ...]:
    """Combine extracted blocks into deterministic chunks without mixing contexts.

    Blocks with different headings, page/table locators, campuses, terms,
    programs, or effective dates are kept apart. Oversized blocks are split at
    whitespace boundaries; table rows are kept in their own chunks when possible.
    Repeating the call with the same blocks and options returns identical chunks.
    """
    if max_chars <= 0:
        raise ValueError("max_chars must be greater than zero")
    if not chunking_version.strip():
        raise ValueError("chunking_version must not be blank")

    chunks: list[Chunk] = []
    current_parts: list[str] = []
    current_length = 0
    current_context: _ChunkContext | None = None

    def flush_current_chunk() -> None:
        """Save the buffered text with its metadata, then reset the buffer."""
        nonlocal current_parts, current_length, current_context
        if not current_parts or current_context is None:
            return

        chunks.append(
            Chunk(
                ordinal=len(chunks),
                content="\n".join(current_parts),
                chunking_version=chunking_version,
                heading_path=current_context.heading_path,
                locator=current_context.locator,
                campus=current_context.campus,
                term=current_context.term,
                program=current_context.program,
                effective_from=current_context.effective_from,
                effective_to=current_context.effective_to,
            )
        )
        current_parts = []
        current_length = 0
        current_context = None

    for block in blocks:
        text = block.text.strip()
        if not text:
            continue

        context = _context_for(block)
        is_table_row = block.kind == BlockKind.TABLE_ROW

        # A table row or changed metadata is a meaningful boundary, not a reason
        # to blend neighboring content into the same searchable excerpt.
        if is_table_row or context != current_context:
            flush_current_chunk()
        current_context = context

        for piece in _split_text(text, max_chars):
            extra_length = len(piece) + (1 if current_parts else 0)
            if current_parts and current_length + extra_length > max_chars:
                flush_current_chunk()
                current_context = context
                extra_length = len(piece)
            current_parts.append(piece)
            current_length += extra_length

        if is_table_row:
            flush_current_chunk()

    flush_current_chunk()
    return tuple(chunks)


def _context_for(block: ExtractedBlock) -> _ChunkContext:
    """Copy one extracted block's structure and applicability into chunk metadata."""
    effective_from, effective_to = _effective_date_range(block)
    heading_path = " > ".join(block.heading_path) or None
    return _ChunkContext(
        heading_path=heading_path,
        locator=block.locator,
        campus=block.campus,
        term=block.term,
        program=block.program,
        effective_from=effective_from,
        effective_to=effective_to,
    )


def _effective_date_range(block: ExtractedBlock) -> tuple[date | None, date | None]:
    """Read an effective date or range only when the block explicitly says it is effective.

    Ordinary event dates and deadlines stay in chunk text; they are not
    mislabeled as a policy's effective period.
    """
    dates = sorted(block.dates)
    if not dates or "effective" not in block.text.casefold():
        return None, None

    effective_text = block.text.casefold().split("effective", maxsplit=1)[1]
    if len(dates) > 1 and _EFFECTIVE_RANGE_MARKER.search(effective_text):
        return dates[0], dates[-1]
    return dates[0], None


def _split_text(text: str, max_chars: int) -> list[str]:
    """Split a long block near spaces so words are not cut in the middle."""
    remaining = text.strip()
    pieces: list[str] = []
    while len(remaining) > max_chars:
        boundary = remaining.rfind(" ", 0, max_chars + 1)
        if boundary <= 0:
            boundary = max_chars
        pieces.append(remaining[:boundary].strip())
        remaining = remaining[boundary:].strip()
    if remaining:
        pieces.append(remaining)
    return pieces
