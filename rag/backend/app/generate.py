from __future__ import annotations

from typing import Any

import httpx

from .config import settings


SYSTEM_PROMPT = (
    "You are a careful RAG assistant. Answer only from the provided context chunks. "
    "Cite source file names in square brackets. If the context is insufficient, say so."
)


def generate_answer(question: str, chunks: list[dict[str, Any]]) -> dict[str, str]:
    if settings.use_openai_generator:
        try:
            return {"mode": "openai", "answer": _openai_answer(question, chunks)}
        except Exception as exc:  # noqa: BLE001 - surface a usable mock fallback
            mock = _mock_answer(question, chunks)
            return {
                "mode": "mock",
                "answer": f"{mock}\n\n(OpenAI generation failed: {exc}. Showing offline answer.)",
            }
    return {"mode": "mock", "answer": _mock_answer(question, chunks)}


def _openai_answer(question: str, chunks: list[dict[str, Any]]) -> str:
    context = "\n\n".join(
        f"[{row['source']} #{row['index']} score={row['score']}]\n{row['text']}" for row in chunks
    )
    payload = {
        "model": settings.openai_model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Question: {question}\n\nContext:\n{context or '(no chunks retrieved)'}",
            },
        ],
    }
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
    with httpx.Client(timeout=60.0) as client:
        response = client.post(f"{settings.openai_base_url}/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()


def _mock_answer(question: str, chunks: list[dict[str, Any]]) -> str:
    if not chunks:
        return (
            "I do not have any indexed documents yet. Load the sample corpus or upload a file, "
            "then ask again."
        )
    top = chunks[0]
    floor = max(0.1, top["score"] * 0.45)
    supporting = [row for row in chunks[1:3] if row["score"] >= floor]
    lines = [
        f"Offline generator (no API key). Best match is [{top['source']}] "
        f"(similarity {top['score']:.2f}) for: {question}",
        "",
        _first_sentences(top["text"]),
    ]
    if supporting:
        lines.append("")
        lines.append("Related passages:")
        for row in supporting:
            lines.append(f"- [{row['source']}] {_first_sentences(row['text'], limit=180)}")
    lines.append("")
    lines.append("Set OPENAI_API_KEY to replace this extractive summary with a real model.")
    return "\n".join(lines)


def _first_sentences(text: str, limit: int = 320) -> str:
    clipped = text.strip()
    if len(clipped) <= limit:
        return clipped
    cut = clipped[:limit]
    if "." in cut:
        cut = cut.rsplit(".", 1)[0] + "."
    return cut.strip()
