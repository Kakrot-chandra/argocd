from __future__ import annotations

import re
from dataclasses import dataclass


_SPLIT_PATTERN = re.compile(r"(?<=[\n.!?])\s+")


@dataclass(frozen=True)
class Chunk:
    text: str
    index: int
    start_char: int
    end_char: int


def chunk_text(text: str, chunk_size: int = 420, chunk_overlap: int = 80) -> list[Chunk]:
    """Split text into overlapping character windows on sentence-ish boundaries."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be >= 0 and < chunk_size")

    cleaned = text.replace("\r\n", "\n").strip()
    if not cleaned:
        return []

    pieces = _split_units(cleaned)
    chunks: list[Chunk] = []
    buf = ""
    buf_start = 0
    cursor = 0

    for piece in pieces:
        piece_start = cleaned.find(piece, cursor)
        if piece_start < 0:
            piece_start = cursor
        cursor = piece_start + len(piece)

        candidate = piece if not buf else f"{buf} {piece}".strip()
        if len(candidate) <= chunk_size or not buf:
            if not buf:
                buf_start = piece_start
            buf = candidate
            continue

        chunks.append(_make_chunk(cleaned, buf, buf_start, len(chunks)))
        overlap = buf[-chunk_overlap:] if chunk_overlap else ""
        overlap_start = buf_start + max(len(buf) - len(overlap), 0)
        buf = f"{overlap} {piece}".strip()
        buf_start = overlap_start if overlap else piece_start

    if buf.strip():
        chunks.append(_make_chunk(cleaned, buf, buf_start, len(chunks)))
    return chunks


def _make_chunk(source: str, text: str, start: int, index: int) -> Chunk:
    text = re.sub(r"\s+", " ", text).strip()
    end = min(len(source), start + len(text))
    return Chunk(text=text, index=index, start_char=max(start, 0), end_char=end)


def _split_units(text: str) -> list[str]:
    parts = [p.strip() for p in _SPLIT_PATTERN.split(text) if p.strip()]
    return parts or [text]
