"""Hierarchy-preserving parsing for legal documents.

Parses Section -> Clause -> Sub-clause structure from extracted document text
before chunking, so that every downstream chunk can be tagged with its position
in the document hierarchy.

Input  (``pages``):  [{"lines": [{"text", "size", "bold"}], "page": int | None}]
Output (``blocks``): [{"text", "page", "section", "clause", "subclause"}]

``size`` is the line's font size in points (PDF) or ``None`` (DOCX, which has no
reliable size). ``bold`` is a best-effort boolean. ``section``/``clause``/
``subclause`` are ``None`` when not detected.
"""

import re
import statistics

# --- Numbering patterns (checked top-to-bottom against each line's start) ------
# Order matters: more specific / deeper patterns are tried before shallower ones
# so that e.g. "1.1.a" is not mistaken for the clause "1.1".

# "1.1.a Foo" / "1.1.1 Foo" — three or more dotted segments => sub-clause
_SUBCLAUSE_DOTTED = re.compile(r"^\s*(\d+\.\d+\.[A-Za-z0-9]+)\s+")
# "1.1 Foo" — exactly two dotted segments => clause
_CLAUSE_DOTTED = re.compile(r"^\s*(\d+\.\d+)\s+")
# "1) Foo" — number with closing paren => sub-clause
_SUBCLAUSE_NUMBERPAREN = re.compile(r"^\s*(\d+)\)\s+")
# "1. Foo" — single number with trailing dot => section
_SECTION_DOTTED = re.compile(r"^\s*(\d+)\.\s+")
# "SECTION 1" / "ARTICLE IV" — keyword headings => section
_SECTION_KEYWORD = re.compile(r"^\s*((?:SECTION|ARTICLE)\s+[0-9IVXLCDM]+)\b", re.IGNORECASE)
# "A. Foo" — single uppercase letter with trailing dot => clause
_CLAUSE_LETTER = re.compile(r"^\s*([A-Z])\.\s+")
# "(a) Foo" / "(iv) Foo" — parenthetical => sub-clause (always deepest level).
# Restricted to a single letter or a short roman numeral so multi-word
# annotations like "(CONTINUED)" or "(NOTE)" are not treated as sub-clauses.
_SUBCLAUSE_PAREN = re.compile(r"^\s*(\([A-Za-z]\)|\([ivxlcdm]{1,6}\))\s+")

# A heading detected purely by font (bold / large) should be short.
_MAX_HEADING_WORDS = 8
# Font size multiplier above body text that flags a heading.
_HEADING_SIZE_RATIO = 1.15


def _match_numbering(text: str):
    """Return (level, label) for a numbering match, or (None, None).

    ``level`` is one of "section", "clause", "subclause".
    """
    m = _SUBCLAUSE_DOTTED.match(text)
    if m:
        return "subclause", m.group(1)
    m = _CLAUSE_DOTTED.match(text)
    if m:
        return "clause", m.group(1)
    m = _SUBCLAUSE_NUMBERPAREN.match(text)
    if m:
        return "subclause", m.group(1)
    m = _SECTION_DOTTED.match(text)
    if m:
        return "section", m.group(1)
    m = _SECTION_KEYWORD.match(text)
    if m:
        return "section", m.group(1).strip()
    m = _CLAUSE_LETTER.match(text)
    if m:
        return "clause", m.group(1)
    m = _SUBCLAUSE_PAREN.match(text)
    if m:
        return "subclause", m.group(1)
    return None, None


def _body_size(lines: list[dict]) -> float | None:
    """Most common font size on a page, used as the 'body text' baseline."""
    sizes = [round(line["size"], 1) for line in lines if line.get("size")]
    if not sizes:
        return None
    try:
        return statistics.mode(sizes)
    except statistics.StatisticsError:
        return statistics.median(sizes)


def _is_font_heading(line: dict, body_size: float | None, page: int | None) -> bool:
    """Best-effort heading detection from font metadata (PDF only).

    A line is treated as a section heading when it is short and is either bold or
    rendered noticeably larger than the page body text.

    The fallback is suppressed on PDF page 1, which is typically a title page
    ("Sample Contract", "PROFESSIONAL SERVICES AGREEMENT") whose short bold lines
    would otherwise be misdetected as sections. DOCX (page is None) is unaffected,
    and numbered headings still match via _match_numbering regardless of page.
    """
    if page is not None and page <= 1:
        return False
    text = line["text"].strip()
    if not text or len(text.split()) > _MAX_HEADING_WORDS:
        return False
    if line.get("bold"):
        return True
    size = line.get("size")
    if size and body_size and size >= body_size * _HEADING_SIZE_RATIO:
        return True
    return False


def parse_pages(pages: list[dict]) -> list[dict]:
    """Parse hierarchy-tagged blocks from per-line page data.

    Walks lines top-to-bottom maintaining a running hierarchy stack. Whenever the
    hierarchy changes (or the page changes), the accumulated body text is flushed
    as a block tagged with the hierarchy state that produced it.
    """
    blocks: list[dict] = []
    current = {"section": None, "clause": None, "subclause": None}

    buffer: list[str] = []
    buffer_page = None
    buffer_tags = dict(current)

    def flush():
        nonlocal buffer
        text = "\n".join(buffer).strip()
        if text:
            blocks.append({
                "text": text,
                "page": buffer_page,
                **buffer_tags,
            })
        buffer = []

    for page_data in pages:
        page = page_data.get("page")
        lines = page_data.get("lines", [])
        body_size = _body_size(lines)

        # Page boundary: flush so blocks don't span pages (page metadata stays accurate).
        if buffer and page != buffer_page:
            flush()

        for line in lines:
            text = (line.get("text") or "").strip()
            if not text:
                continue

            level, label = _match_numbering(text)

            if level is None and _is_font_heading(line, body_size, page):
                level, label = "section", text

            if level is not None:
                # Hierarchy transition -> close out the previous block first.
                flush()
                if level == "section":
                    current = {"section": label, "clause": None, "subclause": None}
                elif level == "clause":
                    current = {"section": current["section"], "clause": label, "subclause": None}
                else:  # subclause
                    current = {
                        "section": current["section"],
                        "clause": current["clause"],
                        "subclause": label,
                    }
                buffer_tags = dict(current)
                buffer_page = page

            if not buffer:
                buffer_page = page
                buffer_tags = dict(current)
            buffer.append(text)

    flush()
    return blocks
