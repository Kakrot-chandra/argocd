from __future__ import annotations

from app.chunking import chunk_text


SAMPLE = (
    "NovaBrew Aero Carafe is a 1.2 liter thermal carafe coffee maker. "
    "It brews at 96C and holds heat for four hours. "
    "Descale every 40 brew cycles. Use vinegar and water. "
    "E1 means the lid sensor is open. E4 means the heater overheated. "
    "The heating element is covered for 24 months."
)


def test_empty_text_returns_no_chunks() -> None:
    assert chunk_text("   ") == []


def test_short_text_is_single_chunk() -> None:
    chunks = chunk_text("Hello world.", chunk_size=420, chunk_overlap=80)
    assert len(chunks) == 1
    assert chunks[0].index == 0
    assert "Hello world" in chunks[0].text


def test_long_text_splits_and_overlaps() -> None:
    text = " ".join(f"Sentence number {i} about irrigation valves and rain sensors." for i in range(40))
    chunks = chunk_text(text, chunk_size=180, chunk_overlap=40)
    assert len(chunks) >= 3
    for chunk in chunks:
        assert 0 < len(chunk.text) <= 180 + 20  # small slack for joining spaces
    # Overlap: some token from chunk n should appear in n+1
    overlap_hits = 0
    for left, right in zip(chunks, chunks[1:]):
        tail = set(left.text.split()[-6:])
        head = set(right.text.split()[:10])
        if tail & head:
            overlap_hits += 1
    assert overlap_hits >= 1


def test_sample_faq_produces_multiple_chunks() -> None:
    chunks = chunk_text(SAMPLE, chunk_size=120, chunk_overlap=30)
    assert len(chunks) >= 2
    joined = " ".join(c.text for c in chunks)
    assert "Descale" in joined
    assert "E4" in joined
