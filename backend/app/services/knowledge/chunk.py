"""Split extracted text into overlapping chunks of about 500–800 tokens."""

from app.services.knowledge.limits import (
    APPROX_CHARS_PER_TOKEN,
    CHUNK_OVERLAP_RATIO,
    TARGET_CHUNK_TOKENS,
)


def chunk_text(text: str) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []
    target_tokens = TARGET_CHUNK_TOKENS
    overlap_ratio = CHUNK_OVERLAP_RATIO
    if not 500 <= target_tokens <= 800:
        raise ValueError("Chunk size must stay between 500 and 800 tokens.")
    if not 0.10 <= overlap_ratio <= 0.20:
        raise ValueError("Chunk overlap must stay between 10% and 20%.")

    size = target_tokens * APPROX_CHARS_PER_TOKEN
    overlap = int(size * overlap_ratio)
    if len(cleaned) <= size:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    length = len(cleaned)
    while start < length:
        end = min(start + size, length)
        if end < length:
            end = _prefer_break(cleaned, start, end)
            if end <= start:
                end = min(start + size, length)
        piece = cleaned[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= length:
            break
        start = max(end - overlap, start + 1)
    return chunks


def _prefer_break(text: str, start: int, end: int) -> int:
    window = text[start:end]
    earliest = int(len(window) * 0.6)
    for separator in ("\n\n", "\n", ". "):
        index = window.rfind(separator, earliest)
        if index != -1:
            return start + index + len(separator)
    space = window.rfind(" ", earliest)
    if space != -1:
        return start + space + 1
    return end
