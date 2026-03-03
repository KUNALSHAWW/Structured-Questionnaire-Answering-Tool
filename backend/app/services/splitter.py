"""Passage splitting – split reference texts into overlapping chunks."""

from app.config import PASSAGE_TOKEN_SIZE, PASSAGE_OVERLAP


def split_into_passages(
    text: str,
    filename: str,
    token_size: int = PASSAGE_TOKEN_SIZE,
    overlap: int = PASSAGE_OVERLAP,
) -> list[dict]:
    """Split text into overlapping passages.

    Returns list of {text, page_or_para, token_count}.
    Attempts page-based splitting first (for PDFs with form-feeds or
    "Page N" markers), otherwise paragraph-based.
    """
    # Try page-based split (form-feed)
    pages = text.split("\f")
    if len(pages) <= 1:
        # Try "Page N" markers
        import re
        parts = re.split(r"(?i)(?:^|\n)page\s+\d+", text)
        if len(parts) > 1:
            pages = parts
        else:
            pages = None

    passages: list[dict] = []

    if pages and len(pages) > 1:
        for page_num, page_text in enumerate(pages, start=1):
            page_text = page_text.strip()
            if not page_text:
                continue
            chunks = _chunk_text(page_text, token_size, overlap)
            for chunk in chunks:
                passages.append(
                    {
                        "text": chunk,
                        "page_or_para": f"page {page_num}",
                        "token_count": len(chunk.split()),
                    }
                )
    else:
        # paragraph-based
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

        current_chunk = ""
        para_start = 1
        current_para = 1
        for i, para in enumerate(paragraphs, start=1):
            candidate = (current_chunk + "\n\n" + para).strip() if current_chunk else para
            if len(candidate.split()) > token_size and current_chunk:
                passages.append(
                    {
                        "text": current_chunk.strip(),
                        "page_or_para": f"paragraph {para_start}",
                        "token_count": len(current_chunk.split()),
                    }
                )
                # overlap: keep tail words
                tail_words = current_chunk.split()[-overlap:]
                current_chunk = " ".join(tail_words) + "\n\n" + para
                para_start = max(1, i - 1)
            else:
                current_chunk = candidate

        if current_chunk.strip():
            passages.append(
                {
                    "text": current_chunk.strip(),
                    "page_or_para": f"paragraph {para_start}",
                    "token_count": len(current_chunk.split()),
                }
            )

    return passages


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
