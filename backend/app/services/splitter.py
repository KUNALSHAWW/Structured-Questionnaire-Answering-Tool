"""Passage splitting – split reference texts into overlapping chunks."""

import re
from app.config import PASSAGE_TOKEN_SIZE, PASSAGE_OVERLAP

# Matches numbered section headers: "1. Title", "2. Title", "Section 3:", etc.
_SECTION_HEADER_RE = re.compile(
    r"^(?:(?:Section\s+)?\d+[\.\):]?\s+[A-Z])",
    re.MULTILINE,
)


def split_into_passages(
    text: str,
    filename: str,
    token_size: int = PASSAGE_TOKEN_SIZE,
    overlap: int = PASSAGE_OVERLAP,
) -> list[dict]:
    """Split text into overlapping passages.

    Returns list of {text, page_or_para, token_count}.

    Strategy (in priority order):
    1. Page-based split (form-feed characters or "Page N" markers)
    2. Section-header-based split ("1. Title", "2. Title", ...)
    3. Double-newline paragraph split
    4. Single-newline fallback
    Within each strategy, oversized blocks are sub-chunked via _chunk_text().
    """
    passages: list[dict] = []

    # ---- Strategy 1: Page-based (form-feed or "Page N") ----
    pages = text.split("\f")
    if len(pages) <= 1:
        parts = re.split(r"(?i)(?:^|\n)page\s+\d+", text)
        if len(parts) > 1:
            pages = parts
        else:
            pages = None

    if pages and len(pages) > 1:
        for page_num, page_text in enumerate(pages, start=1):
            page_text = page_text.strip()
            if not page_text:
                continue
            # Try to split each page further by sections
            sections = _split_by_sections(page_text)
            if len(sections) > 1:
                for sec_num, sec_text in sections:
                    chunks = _chunk_text(sec_text, token_size, overlap)
                    for ci, chunk in enumerate(chunks):
                        label = f"page {page_num}, section {sec_num}"
                        if len(chunks) > 1:
                            label += f" (part {ci + 1})"
                        passages.append({
                            "text": chunk,
                            "page_or_para": label,
                            "token_count": len(chunk.split()),
                        })
            else:
                chunks = _chunk_text(page_text, token_size, overlap)
                for ci, chunk in enumerate(chunks):
                    label = f"page {page_num}"
                    if len(chunks) > 1:
                        label += f" (part {ci + 1})"
                    passages.append({
                        "text": chunk,
                        "page_or_para": label,
                        "token_count": len(chunk.split()),
                    })
        return passages

    # ---- Strategy 2: Section-header-based ----
    sections = _split_by_sections(text)
    if len(sections) > 1:
        for sec_num, sec_text in sections:
            chunks = _chunk_text(sec_text, token_size, overlap)
            for ci, chunk in enumerate(chunks):
                label = f"section {sec_num}"
                if len(chunks) > 1:
                    label += f" (part {ci + 1})"
                passages.append({
                    "text": chunk,
                    "page_or_para": label,
                    "token_count": len(chunk.split()),
                })
        return passages

    # ---- Strategy 3 & 4: Paragraph-based ----
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paragraphs) <= 1:
        # Single-newline fallback: group single-newline-separated lines
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    current_chunk = ""
    para_start = 1
    for i, para in enumerate(paragraphs, start=1):
        candidate = (current_chunk + "\n\n" + para).strip() if current_chunk else para
        if len(candidate.split()) > token_size and current_chunk:
            # Flush current_chunk
            _append_chunks(passages, current_chunk.strip(), para_start, token_size, overlap)
            # Overlap: keep tail words for continuity
            tail_words = current_chunk.split()[-overlap:]
            current_chunk = " ".join(tail_words) + "\n\n" + para
            para_start = max(1, i - 1)
        elif len(candidate.split()) > token_size and not current_chunk:
            # Single paragraph bigger than token_size — force-chunk it
            _append_chunks(passages, candidate, i, token_size, overlap)
            current_chunk = ""
            para_start = i + 1
        else:
            current_chunk = candidate

    if current_chunk.strip():
        _append_chunks(passages, current_chunk.strip(), para_start, token_size, overlap)

    return passages


def _split_by_sections(text: str) -> list[tuple[int, str]]:
    """Split text at numbered section headers.

    Returns list of (section_number, section_text).
    If no section headers found, returns empty list.
    """
    # Find all positions where a numbered section starts
    header_positions = []
    for m in re.finditer(r"(?:^|\n)((?:Section\s+)?(\d+)[\.\):]?\s+[A-Z])", text, re.MULTILINE):
        sec_num = int(m.group(2))
        start = m.start()
        if m.group(0).startswith("\n"):
            start += 1
        header_positions.append((start, sec_num))

    if len(header_positions) < 2:
        return []

    sections = []
    for idx, (pos, sec_num) in enumerate(header_positions):
        end = header_positions[idx + 1][0] if idx + 1 < len(header_positions) else len(text)
        sec_text = text[pos:end].strip()
        if sec_text:
            sections.append((sec_num, sec_text))
    return sections


def _append_chunks(
    passages: list[dict],
    text: str,
    para_start: int,
    token_size: int,
    overlap: int,
) -> None:
    """Sub-chunk text if needed and append to passages list."""
    chunks = _chunk_text(text, token_size, overlap)
    for ci, chunk in enumerate(chunks):
        label = f"paragraph {para_start}"
        if len(chunks) > 1:
            label += f" (part {ci + 1})"
        passages.append({
            "text": chunk,
            "page_or_para": label,
            "token_count": len(chunk.split()),
        })


def _chunk_text(text: str, token_size: int, overlap: int) -> list[str]:
    """Split a text block into token-sized chunks with overlap."""
    words = text.split()
    if len(words) <= token_size:
        return [text]
    chunks = []
    start = 0
    while start < len(words):
        end = start + token_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap
    return chunks
