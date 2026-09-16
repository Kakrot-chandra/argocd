from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import settings
from .pipeline import RagPipeline
from .store import IndexStore

store = IndexStore()
pipeline = RagPipeline(store)

app = FastAPI(title="NovaRAG", version="1.0.0", description="Retrieval-augmented generation from scratch.")
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if origins == ["*"] else origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryBody(BaseModel):
    question: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=12)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "service": "novarag"}


@app.get("/api/status")
def status() -> dict:
    return store.status()


@app.get("/api/documents")
def documents() -> dict:
    docs = [
        {
            "id": d.id,
            "name": d.name,
            "topic": d.topic,
            "source": d.source,
            "chars": len(d.text),
        }
        for d in store.documents.values()
    ]
    return {"documents": docs}


@app.post("/api/ingest/samples")
def ingest_samples() -> dict:
    try:
        return pipeline.ingest_samples()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/ingest/upload")
async def ingest_upload(files: list[UploadFile] = File(...)) -> dict:
    payload: list[tuple[str, str]] = []
    for upload in files:
        name = upload.filename or "upload.txt"
        if not name.lower().endswith((".txt", ".md")):
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {name}")
        raw = await upload.read()
        payload.append((name, raw.decode("utf-8", errors="replace")))
    if not payload:
        raise HTTPException(status_code=400, detail="No files uploaded")
    return pipeline.ingest_uploads(payload)


@app.post("/api/query")
def query(body: QueryBody) -> dict:
    if not store.chunks:
        raise HTTPException(status_code=409, detail="Index is empty. Load sample documents first.")
    return pipeline.query(body.question.strip(), body.top_k)


@app.delete("/api/index")
def reset_index() -> dict:
    store.reset()
    return store.status()
