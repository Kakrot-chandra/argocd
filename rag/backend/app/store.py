from __future__ import annotations

import json
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import settings
from .embeddings import TfidfEmbedder


@dataclass
class Document:
    id: str
    name: str
    topic: str
    source: str
    text: str
    created_at: str


@dataclass
class StoredChunk:
    id: str
    doc_id: str
    doc_name: str
    topic: str
    index: int
    text: str
    start_char: int
    end_char: int
    embedding: list[float] = field(default_factory=list)


class IndexStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings.index_path
        self._lock = threading.Lock()
        self.documents: dict[str, Document] = {}
        self.chunks: list[StoredChunk] = []
        self.embedder = TfidfEmbedder()
        self.updated_at: str | None = None
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self.documents = {d["id"]: Document(**d) for d in raw.get("documents", [])}
        self.chunks = [StoredChunk(**c) for c in raw.get("chunks", [])]
        self.embedder.load_state(raw.get("embedder") or {})
        self.updated_at = raw.get("updated_at")

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "updated_at": self.updated_at,
            "documents": [asdict(d) for d in self.documents.values()],
            "chunks": [asdict(c) for c in self.chunks],
            "embedder": self.embedder.to_state(),
        }
        self.path.write_text(json.dumps(payload), encoding="utf-8")

    def reset(self) -> None:
        with self._lock:
            self.documents = {}
            self.chunks = []
            self.embedder = TfidfEmbedder()
            self.updated_at = None
            if self.path.exists():
                self.path.unlink()

    def replace_all(self, documents: list[Document], chunks: list[StoredChunk]) -> None:
        with self._lock:
            self.documents = {d.id: d for d in documents}
            self.chunks = chunks
            self.updated_at = datetime.now(timezone.utc).isoformat()
            if not settings.use_openai_embeddings:
                self.embedder.fit(c.text for c in chunks)
                for chunk in self.chunks:
                    chunk.embedding = self.embedder.embed(chunk.text)
            self.save()

    def status(self) -> dict[str, Any]:
        return {
            "document_count": len(self.documents),
            "chunk_count": len(self.chunks),
            "updated_at": self.updated_at,
            "index_path": str(self.path),
            "embedder": settings.embedder_mode,
            "generator": settings.generator_mode,
            "ready": bool(self.chunks),
        }


def new_document(name: str, text: str, topic: str = "uploaded", source: str = "upload") -> Document:
    return Document(
        id=str(uuid.uuid4()),
        name=name,
        topic=topic,
        source=source,
        text=text,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
