import re
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from io import BytesIO
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup, Tag
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from src.models.enums import Campus

# h1-h6 tags represent section titles at six levels of nesting.
_HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
# These HTML tags are treated as meaningful text blocks by the document walker.
_BLOCK_TAGS = [*_HEADING_TAGS, "p", "li", "tr", "form", "blockquote", "pre"]
# Match academic seasons followed by a four-digit year, such as "Fall 2026".
_TERM_PATTERN = re.compile(r"\b(Fall|Spring|Summer|Winter)\s+(20\d{2})\b", re.IGNORECASE)
# Match a program name only when the source explicitly labels it as a program.
_PROGRAM_PATTERN = re.compile(
    r"\bprogram(?: of study)?\s*[:\-]\s*([^\n|;]+?)(?=\s+(?:must|may|should|will|is|are)\b|[.;]|$)",
    re.IGNORECASE,
)
# Match the campus names represented by the Campus enum in the database schema.
_CAMPUS_PATTERN = re.compile(r"\b(Hammond|Westville)\b", re.IGNORECASE)
# Recognize ISO dates, numeric month/day/year dates, and written month-name dates.
_DATE_PATTERNS = (
    re.compile(r"\b20\d{2}-\d{2}-\d{2}\b"),
    re.compile(r"\b\d{1,2}/\d{1,2}/20\d{2}\b"),
    re.compile(
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{1,2},?\s+20\d{2}\b",
        re.IGNORECASE,
    ),
)


class BlockKind(StrEnum):
    """Names the kind of document element represented by an extracted block."""

    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE_ROW = "table_row"
    FORM = "form"
    BLOCKQUOTE = "blockquote"
    PRE = "pre"


class ExtractionError(ValueError):
    """Raised for unsupported input or supported documents that cannot be parsed safely."""


@dataclass(frozen=True)
class ExtractedBlock:
    """One ordered text passage, retaining useful structure and applicability.

    ``heading_path`` records the containing headings; ``locator`` and ``row``
    point back to pages or table rows. The remaining fields hold context found
    directly in the passage, and may be ``None`` when it was not stated.
    """

    kind: BlockKind
    text: str
    heading_path: tuple[str, ...] = ()
    locator: str | None = None
    row: int | None = None
    dates: tuple[date, ...] = ()
    campus: Campus | None = None
    term: str | None = None
    program: str | None = None


@dataclass(frozen=True)
class ExtractedLink:
    """A discovered HTTP(S) link; the extractor records it but never fetches it."""

    url: str
    title: str


@dataclass(frozen=True)
class ExtractedDocument:
    """The ordered text blocks and links found in one input document."""

    blocks: tuple[ExtractedBlock, ...]
    links: tuple[ExtractedLink, ...] = ()


def extract_document(
    content: bytes | str,
    content_type: str,
    *,
    base_url: str | None = None,
) -> ExtractedDocument:
    """Choose an HTML or PDF parser based on the response's media type.

    ``content_type`` may include parameters such as a character encoding.
    ``base_url`` is used only to turn relative HTML links into absolute links.
    Unsupported media types raise ``ExtractionError`` instead of being guessed.
    """
    media_type = content_type.split(";", 1)[0].strip().lower()
    if media_type in {"text/html", "application/xhtml+xml"}:
        return extract_html_document(content, base_url=base_url)
    if media_type == "application/pdf":
        if not isinstance(content, bytes):
            raise ExtractionError("PDF content must be bytes")
        return extract_pdf_document(content)
    raise ExtractionError(f"unsupported content type: {media_type or '<empty>'}")


def extract_html_document(
    content: bytes | str, *, base_url: str | None = None
) -> ExtractedDocument:
    """Extract readable HTML text while preserving headings, tables, forms, and links.

    Table cells are labeled with their column headings. Form descriptions include
    labels and choices but intentionally omit values that could contain personal
    data. Relative links are resolved only when a ``base_url`` is provided.
    """
    # Beautiful Soup turns the HTML string or bytes into a searchable tree of tags.
    soup = BeautifulSoup(content, "html.parser")
    # Scripts and templates are not student-facing document content, so remove their whole subtrees.
    for element in soup.find_all(["script", "style", "noscript", "template"]):
        element.decompose()

    # Full pages have a body; fragments may not, so use the whole parsed document as a fallback.
    root = soup.body or soup
    tables = root.find_all("table")
    # Tag identity lets each row recover its table's caption and headers.
    table_numbers = {id(table): number for number, table in enumerate(tables, start=1)}
    table_headers = {id(table): _table_headers(table) for table in tables}
    table_header_rows = {id(table): _table_header_row(table) for table in tables}
    heading_path: list[str] = []
    table_row_counts: dict[int, int] = {}
    form_numbers: dict[int, int] = {}
    blocks: list[ExtractedBlock] = []

    # find_all walks matching descendants in the order they appear in the document.
    for element in root.find_all(_BLOCK_TAGS):
        if _inside_tag(element, {"form", "li", "table"}, include_self=False):
            if element.name != "tr":
                continue
        if element.name in _HEADING_TAGS:
            level = int(element.name[1])
            heading = _text(element)
            if not heading:
                continue
            heading_path = heading_path[: level - 1]
            heading_path.append(heading)
            blocks.append(_make_block(BlockKind.HEADING, heading, heading_path))
        elif element.name == "tr":
            # A row's nearest table ancestor supplies its caption and column labels.
            table = element.find_parent("table")
            if table is None:
                continue
            table_id = id(table)
            if element is table_header_rows[table_id]:
                continue
            cells = [_text(cell) for cell in element.find_all(["th", "td"], recursive=False)]
            if not any(cells):
                continue
            row_number = table_row_counts.get(table_id, 0) + 1
            table_row_counts[table_id] = row_number
            headers = table_headers[table_id]
            if headers:
                labeled_cells = []
                for cell_index, cell_value in enumerate(cells):
                    header = (
                        headers[cell_index]
                        if cell_index < len(headers) and headers[cell_index]
                        else f"Column {cell_index + 1}"
                    )
                    labeled_cells.append(f"{header}: {cell_value}")
                row_text = " | ".join(labeled_cells)
            else:
                row_text = " | ".join(cells)
            caption = table.find("caption")
            table_label = _text(caption) if caption else f"Table {table_numbers[table_id]}"
            blocks.append(
                _make_block(
                    BlockKind.TABLE_ROW,
                    row_text,
                    heading_path,
                    locator=f"{table_label}, row {row_number}",
                    row=row_number,
                )
            )
        elif element.name == "form":
            form_number = len(form_numbers) + 1
            form_numbers[id(element)] = form_number
            form_text = _extract_form_text(element, form_number)
            if form_text:
                blocks.append(_make_block(BlockKind.FORM, form_text, heading_path))
        else:
            text = _text(element)
            if not text:
                continue
            kind = {
                "li": BlockKind.LIST_ITEM,
                "blockquote": BlockKind.BLOCKQUOTE,
                "pre": BlockKind.PRE,
            }.get(element.name, BlockKind.PARAGRAPH)
            blocks.append(_make_block(kind, text, heading_path))

    links = _extract_links(root, base_url)
    return ExtractedDocument(tuple(blocks), links)


def extract_pdf_document(content: bytes) -> ExtractedDocument:
    """Extract page-located text blocks from a PDF byte string.

    Text is read one page at a time so citations can use visible page numbers.
    Encrypted or malformed files raise ``ExtractionError``; scanned image-only
    pages produce no text because optical character recognition is not performed.
    """
    try:
        # PdfReader expects a file-like object; BytesIO lets it read the in-memory response bytes.
        reader = PdfReader(BytesIO(content), strict=False)
        if reader.is_encrypted:
            raise ExtractionError("encrypted PDF documents are not supported")
        blocks: list[ExtractedBlock] = []
        # Page numbers are one-based to match the labels people see in PDF viewers.
        for page_number, page in enumerate(reader.pages, start=1):
            # Layout mode keeps columns closer to their visual arrangement; plain text is fallback.
            text = page.extract_text(extraction_mode="layout") or page.extract_text() or ""
            page_blocks = _pdf_page_blocks(text, page_number)
            blocks.extend(page_blocks)
    except ExtractionError:
        raise
    except (PdfReadError, OSError) as error:
        raise ExtractionError("unable to parse PDF document") from error
    return ExtractedDocument(tuple(blocks))


def _pdf_page_blocks(text: str, page_number: int) -> list[ExtractedBlock]:
    """Turn one PDF page's extracted text into paragraphs and an optional heading.

    A short title-like first line is treated as the page heading. Remaining
    non-empty lines are joined into paragraphs, all tagged with the page number.
    """
    lines = [line.strip() for line in text.splitlines()]
    nonempty = [line for line in lines if line]
    if not nonempty:
        return []

    first_line = nonempty[0]
    heading_path: tuple[str, ...] = ()
    if _looks_like_heading(first_line):
        heading_path = (first_line,)
        content_lines = nonempty[1:]
        blocks = [
            _make_block(BlockKind.HEADING, first_line, heading_path, locator=f"Page {page_number}")
        ]
    else:
        content_lines = nonempty
        blocks = []

    for paragraph in _paragraphs(content_lines):
        blocks.append(
            _make_block(
                BlockKind.PARAGRAPH,
                paragraph,
                heading_path,
                locator=f"Page {page_number}",
            )
        )
    return blocks


def _looks_like_heading(line: str) -> bool:
    """Use a small text heuristic to recognize likely PDF titles or headings."""
    words = line.split()
    return (
        len(line) <= 100
        and 1 <= len(words) <= 12
        and not line.endswith((".", ";", "?", "!"))
        and (line.isupper() or line.istitle())
    )


def _paragraphs(lines: list[str]) -> list[str]:
    """Join adjacent non-empty lines and start a new paragraph at each blank line."""
    paragraphs: list[str] = []
    current: list[str] = []
    for line in lines:
        if line:
            current.append(line)
        elif current:
            paragraphs.append(" ".join(current))
            current = []
    if current:
        paragraphs.append(" ".join(current))
    return paragraphs


def _make_block(
    kind: BlockKind,
    text: str,
    heading_path: list[str] | tuple[str, ...],
    *,
    locator: str | None = None,
    row: int | None = None,
) -> ExtractedBlock:
    """Create a block and derive date, campus, term, and program hints from its text."""
    return ExtractedBlock(
        kind=kind,
        text=text,
        heading_path=tuple(heading_path),
        locator=locator,
        row=row,
        dates=_extract_dates(text),
        campus=_extract_campus(text),
        term=_extract_term(text),
        program=_extract_program(text),
    )


def _extract_dates(text: str) -> tuple[date, ...]:
    """Find valid dates in supported numeric and month-name formats, without duplicates."""
    found: list[date] = []
    for pattern in _DATE_PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(0)
            parsed: date | None = None
            for date_format in ("%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y", "%B %d %Y"):
                try:
                    parsed = datetime.strptime(value, date_format).date()
                    break
                except ValueError:
                    continue
            if parsed is not None and parsed not in found:
                found.append(parsed)
    return tuple(found)


def _extract_campus(text: str) -> Campus | None:
    """Return Hammond or Westville when either campus name appears in the text."""
    match = _CAMPUS_PATTERN.search(text)
    return Campus(match.group(1).lower()) if match else None


def _extract_term(text: str) -> str | None:
    """Return a normalized academic term such as ``Fall 2026`` when present."""
    match = _TERM_PATTERN.search(text)
    return f"{match.group(1).title()} {match.group(2)}" if match else None


def _extract_program(text: str) -> str | None:
    """Read the value following an explicit ``Program:`` or ``Program of Study:`` label."""
    match = _PROGRAM_PATTERN.search(text)
    return match.group(1).strip() if match else None


def _table_headers(table: Tag) -> list[str]:
    """Return the direct cell text from a table's recognized header row."""
    header_row = _table_header_row(table)
    if header_row is None:
        return []
    return [_text(cell) for cell in header_row.find_all(["th", "td"], recursive=False)]


def _table_header_row(table: Tag) -> Tag | None:
    """Find a table header row, supporting both modern and older HTML markup."""
    # CSS selectors are a compact way to find a row inside a table's explicit header section.
    header_row = table.select_one("thead tr")
    if header_row is None:
        # Older tables often use header cells in their first row without a thead wrapper.
        rows = table.find_all("tr")
        if rows and rows[0].find_all("th", recursive=False):
            header_row = rows[0]
    return header_row


def _extract_form_text(form: Tag, form_number: int) -> str:
    """Describe form fields and choices without copying any entered field values."""
    # Match labels to controls by their HTML for/id attributes; never include user-entered values.
    labels = {
        label.get("for"): _text(label)
        for label in form.find_all("label")
        if label.get("for") and _text(label)
    }
    fields: list[str] = []
    for control in form.find_all(["input", "select", "textarea", "button"]):
        name = control.get("name") or control.get("id")
        label = (
            labels.get(control.get("id")) or control.get("aria-label") or name or "Unlabeled field"
        )
        control_type = control.get("type") or control.name
        description = f"{label} ({control_type})"
        if control.name == "select":
            options = [_text(option) for option in control.find_all("option") if _text(option)]
            if options:
                description += ": " + ", ".join(options)
        fields.append(description)
    if not fields:
        return ""
    title = _text(form.find(["legend", "h1", "h2", "h3"])) or f"Form {form_number}"
    return f"{title}. Fields: " + "; ".join(fields)


def _extract_links(root: Tag, base_url: str | None) -> tuple[ExtractedLink, ...]:
    """Return distinct HTTP(S) links in an HTML tree, resolving relative links when possible."""
    if base_url is None:
        return ()
    links: list[ExtractedLink] = []
    seen: set[str] = set()
    for anchor in root.find_all(["a", "area"], href=True):
        # Resolve relative hrefs, but record links rather than fetching them here.
        target = urljoin(base_url, anchor["href"].strip())
        parsed = urlsplit(target)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or target in seen:
            continue
        seen.add(target)
        title = _text(anchor) or anchor.get("aria-label") or anchor.get("title") or target
        links.append(ExtractedLink(url=target, title=title))
    return tuple(links)


def _inside_tag(element: Tag, names: set[str], *, include_self: bool) -> bool:
    """Check whether an HTML tag is inside one of the named ancestor tags.

    ``include_self`` controls whether ``element`` itself is checked before its
    parents. This lets the HTML walker avoid re-extracting nested text blocks.
    """
    parent = element if include_self else element.parent
    while isinstance(parent, Tag):
        if parent.name in names:
            return True
        parent = parent.parent
    return False


def _text(element: Tag | None) -> str:
    """Get visible text from a Beautiful Soup tag and collapse whitespace between pieces."""
    if element is None:
        return ""
    # stripped_strings yields visible text pieces without HTML tags or surrounding whitespace.
    return " ".join(element.stripped_strings)
