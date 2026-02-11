from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ChunkPiece:
    text: str
    section: str | None = None
    subsection: str | None = None


HEADING_RE = re.compile(
    r"^(?:\d+(?:\.\d+){0,4}|[A-Z][A-Z0-9 \-/]{4,}|(?:Chapter|CHAPTER|Section|SECTION)\s+\w+)\b"
)
SUBSECTION_RE = re.compile(r"^\d+(?:\.\d+){1,6}\b")


def _chunk_with_overlap(text: str, chunk_size: int, overlap: int) -> List[str]:
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


def chunk_text(
    text: str,
    chunk_size: int = 1200,
    overlap: int = 180,
    max_chars: Optional[int] = None,
) -> List[str]:
    if max_chars is not None:
        chunk_size = max_chars
    cleaned = text.replace("\r", "\n").strip()
    if not cleaned:
        return []
    return _chunk_with_overlap(cleaned, chunk_size=chunk_size, overlap=overlap)


def chunk_policy_text(
    text: str,
    chunk_size: int = 1200,
    overlap: int = 180,
) -> List[ChunkPiece]:
    """
    Heading-aware chunking for policy documents.
    Captures nearest section/subsection metadata for each chunk.
    """
    cleaned = text.replace("\r", "\n").strip()
    if not cleaned:
        return []

    lines = cleaned.split("\n")
    current_section: str | None = None
    current_subsection: str | None = None
    segment_lines: list[str] = []
    segments: list[tuple[str, str | None, str | None]] = []

    def flush_segment() -> None:
        if not segment_lines:
            return
        segment_text = "\n".join(segment_lines).strip()
        if segment_text:
            segments.append((segment_text, current_section, current_subsection))
        segment_lines.clear()

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        if HEADING_RE.match(line):
            flush_segment()
            current_section = line[:180]
            if SUBSECTION_RE.match(line):
                current_subsection = line[:120]
            else:
                current_subsection = None
            segment_lines.append(line)
            continue

        if SUBSECTION_RE.match(line):
            flush_segment()
            current_subsection = line[:120]
            segment_lines.append(line)
            continue

        segment_lines.append(line)

    flush_segment()

    if not segments:
        return [ChunkPiece(text=ch) for ch in _chunk_with_overlap(cleaned, chunk_size=chunk_size, overlap=overlap)]

    pieces: list[ChunkPiece] = []
    for segment_text, section, subsection in segments:
        for chunk in _chunk_with_overlap(segment_text, chunk_size=chunk_size, overlap=overlap):
            ch = chunk.strip()
            if ch:
                pieces.append(ChunkPiece(text=ch, section=section, subsection=subsection))
    return pieces
