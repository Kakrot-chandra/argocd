from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable

import httpx

from .config import settings


_TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    words = _TOKEN.findall(text.lower())
    grams = list(words)
    grams.extend(f"{a}_{b}" for a, b in zip(words, words[1:]))
    return grams


class TfidfEmbedder:
    """Corpus TF-IDF vectors. Fast, offline, good enough for a small demo corpus."""

    def __init__(self) -> None:
        self.idf: dict[str, float] = {}
        self.vocab: dict[str, int] = {}

    def fit(self, texts: Iterable[str]) -> None:
        docs = [tokenize(t) for t in texts]
        df: Counter[str] = Counter()
        for tokens in docs:
            df.update(set(tokens))
        n = max(len(docs), 1)
        self.idf = {term: math.log((1 + n) / (1 + count)) + 1.0 for term, count in df.items()}
        self.vocab = {term: i for i, term in enumerate(sorted(self.idf))}

    def embed(self, text: str) -> list[float]:
        if not self.vocab:
            return []
        tf = Counter(tokenize(text))
        vec = [0.0] * len(self.vocab)
        for term, count in tf.items():
            idx = self.vocab.get(term)
            if idx is None:
                continue
            vec[idx] = (count / max(sum(tf.values()), 1)) * self.idf.get(term, 0.0)
        return _l2_normalize(vec)

    def embed_many(self, texts: Iterable[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]

    def to_state(self) -> dict:
        return {"idf": self.idf, "vocab": self.vocab}

    def load_state(self, state: dict) -> None:
        self.idf = {str(k): float(v) for k, v in (state.get("idf") or {}).items()}
        self.vocab = {str(k): int(v) for k, v in (state.get("vocab") or {}).items()}


class OpenAIEmbedder:
    def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
        payload = {"model": settings.openai_embed_model, "input": texts}
        with httpx.Client(timeout=60.0) as client:
            response = client.post(f"{settings.openai_base_url}/embeddings", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()["data"]
        data.sort(key=lambda row: row["index"])
        return [_l2_normalize(row["embedding"]) for row in data]

    def embed(self, text: str) -> list[float]:
        return self.embed_many([text])[0]


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return float(sum(x * y for x, y in zip(a, b)))


def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0:
        return vec
    return [x / norm for x in vec]
