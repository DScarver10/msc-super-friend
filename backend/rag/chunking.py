from __future__ import annotations

from typing import List


def chunk_text(text: str, chunk_size: int = 1400, overlap: int = 200) -> List[str]:
    """
    Simple char-based chunking.
    Production improvement: token-based chunking using tiktoken.
    """
    text = text.replace("\r", "\n").strip()
    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = max(0, end - overlap)

    return chunks
