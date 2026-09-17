from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

from .chunking import chunk_text
from .config import settings
from .embeddings import OpenAIEmbedder, cosine
from .generate import generate_answer
from .store import Document, IndexStore, StoredChunk, new_document


StageFn = Callable[[], Any]


def timed(stage: str, fn: StageFn) -> dict[str, Any]:
    started = time.perf_counter()
    result = fn()
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    return {"stage": stage, "ms": elapsed_ms, "result": result}


class RagPipeline:
    def __init__(self, store: IndexStore | None = None) -> None:
        self.store = store or IndexStore()

    def ingest_paths(self, paths: list[Path], source: str = "sample") -> dict[str, Any]:
        stages: list[dict[str, Any]] = []

        def _load() -> list[Document]:
            docs: list[Document] = []
            for path in paths:
                text = path.read_text(encoding="utf-8")
                topic = path.stem.split("-")[0] if "-" in path.stem else path.stem
                docs.append(new_document(path.name, text, topic=topic, source=source))
            return docs

        load_stage = timed("ingest", _load)
        documents: list[Document] = load_stage.pop("result")
        stages.append(load_stage)

        def _chunk() -> list[StoredChunk]:
            chunks: list[StoredChunk] = []
            for doc in documents:
                for piece in chunk_text(doc.text, settings.chunk_size, settings.chunk_overlap):
                    chunks.append(
                        StoredChunk(
                            id=f"{doc.id}:{piece.index}",
                            doc_id=doc.id,
                            doc_name=doc.name,
                            topic=doc.topic,
                            index=piece.index,
                            text=piece.text,
                            start_char=piece.start_char,
                            end_char=piece.end_char,
                        )
                    )
            return chunks

        chunk_stage = timed("chunk", _chunk)
        chunks: list[StoredChunk] = chunk_stage.pop("result")
        stages.append(chunk_stage)

        def _embed_and_index() -> int:
            if settings.use_openai_embeddings:
                vectors = OpenAIEmbedder().embed_many([c.text for c in chunks])
                for chunk, vector in zip(chunks, vectors):
                    chunk.embedding = vector
            self.store.replace_all(documents, chunks)
            return len(chunks)

        embed_stage = timed("embed", _embed_and_index)
        embed_stage["chunks"] = embed_stage.pop("result")
        stages.append(embed_stage)
        stages.append({"stage": "index", "ms": 0, "ready": True, "documents": len(documents)})
        return {"documents": [doc.__dict__ for doc in documents], "chunk_count": len(chunks), "pipeline": stages}

    def ingest_samples(self) -> dict[str, Any]:
        sample_dir = settings.sample_dir
        paths = sorted(p for p in sample_dir.glob("*") if p.suffix.lower() in {".md", ".txt"})
        if not paths:
            raise FileNotFoundError(f"No sample documents in {sample_dir}")
        return self.ingest_paths(paths, source="sample")

    def ingest_uploads(self, files: list[tuple[str, str]]) -> dict[str, Any]:
        existing = list(self.store.documents.values())
        new_docs = [new_document(name, text, topic="uploaded", source="upload") for name, text in files]
        merged_docs = existing + new_docs
        # Re-chunk everything so TF-IDF idf stays consistent.
        chunks: list[StoredChunk] = []
        for doc in merged_docs:
            for piece in chunk_text(doc.text, settings.chunk_size, settings.chunk_overlap):
                chunks.append(
                    StoredChunk(
                        id=f"{doc.id}:{piece.index}",
                        doc_id=doc.id,
                        doc_name=doc.name,
                        topic=doc.topic,
                        index=piece.index,
                        text=piece.text,
                        start_char=piece.start_char,
                        end_char=piece.end_char,
                    )
                )
        if settings.use_openai_embeddings:
            vectors = OpenAIEmbedder().embed_many([c.text for c in chunks])
            for chunk, vector in zip(chunks, vectors):
                chunk.embedding = vector
        self.store.replace_all(merged_docs, chunks)
        return {
            "added": [d.__dict__ for d in new_docs],
            "document_count": len(merged_docs),
            "chunk_count": len(chunks),
            "pipeline": [
                {"stage": "ingest", "ms": 0, "files": len(files)},
                {"stage": "chunk", "ms": 0, "chunks": len(chunks)},
                {"stage": "embed", "ms": 0},
                {"stage": "index", "ms": 0, "ready": True},
            ],
        }

    def retrieve(self, question: str, top_k: int | None = None) -> list[dict[str, Any]]:
        if not self.store.chunks:
            return []
        k = top_k or settings.top_k
        if settings.use_openai_embeddings:
            query_vec = OpenAIEmbedder().embed(question)
        else:
            query_vec = self.store.embedder.embed(question)
        scored = []
        for chunk in self.store.chunks:
            score = cosine(query_vec, chunk.embedding)
            scored.append(
                {
                    "id": chunk.id,
                    "doc_id": chunk.doc_id,
                    "source": chunk.doc_name,
                    "topic": chunk.topic,
                    "index": chunk.index,
                    "text": chunk.text,
                    "score": round(score, 4),
                }
            )
        scored.sort(key=lambda row: row["score"], reverse=True)
        return scored[:k]

    def query(self, question: str, top_k: int | None = None) -> dict[str, Any]:
        retrieve_stage = timed("retrieve", lambda: self.retrieve(question, top_k))
        chunks = retrieve_stage.pop("result")
        generate_stage = timed("generate", lambda: generate_answer(question, chunks))
        generation = generate_stage.pop("result")
        generate_stage["mode"] = generation["mode"]
        return {
            "question": question,
            "answer": generation["answer"],
            "generator": generation["mode"],
            "chunks": chunks,
            "pipeline": [retrieve_stage, generate_stage],
        }
