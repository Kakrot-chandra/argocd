# NovaRAG

End-to-end retrieval-augmented generation you can run locally without a cloud vector database. The existing `gitops-argocd` and `pod-metadata-master` trees in this repository are untouched; this app lives in `rag/`.

Pipeline: **ingest → chunk → embed → index → retrieve → generate**.

## Architecture

```
Browser (Vite/React UI)
        │  /api/*
        ▼
FastAPI  ── chunker (sentence-ish windows)
         ── embedder (local TF-IDF, or OpenAI embeddings if a key is set)
         ── JSON index on disk (cosine retrieval)
         ── generator (offline extractive mock, or OpenAI-compatible chat)
```

- **Sample corpus** (`backend/data/samples/`): five distinct topics so ranking is obvious — NovaBrew coffee FAQ, Northwind remote-work policy, HelioFlow irrigation reset, honey bee colony notes, kitchari recipe.
- **Default embedder**: in-process TF-IDF (no model download). Set `EMBED_BACKEND=openai` plus `OPENAI_API_KEY` to use OpenAI embeddings.
- **Generator**: mock/offline when no key is present; OpenAI-compatible `/chat/completions` when `OPENAI_API_KEY` is set (`OPENAI_BASE_URL` can point at a proxy).

## First commands

```bash
cd rag/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# tests (chunking, retrieval ranking, sample query)
pytest -q

# API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

In another terminal:

```bash
cd rag/frontend
npm install
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173). Click **Load sample documents**, then ask a question.

Production (one process, UI + API) after `npm run build` in `frontend/`:

```bash
cd rag
./scripts/run-cloud.sh
```

Then open [http://127.0.0.1:8080](http://127.0.0.1:8080).

### Index + query without the UI

```bash
# after the API is up
curl -s -X POST http://127.0.0.1:8000/api/ingest/samples | python3 -m json.tool
curl -s -X POST http://127.0.0.1:8000/api/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"How often should I descale the NovaBrew carafe?"}'
```

## Environment

| Variable | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | empty | Enables real generation (and embeddings when `EMBED_BACKEND=auto`) |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible base URL |
| `OPENAI_MODEL` | `gpt-4o-mini` | Chat model |
| `OPENAI_EMBED_MODEL` | `text-embedding-3-small` | Embedding model |
| `EMBED_BACKEND` | `auto` | `auto` / `tfidf` / `openai` |
| `RAG_FORCE_MOCK` | `false` | Force offline generator even if a key exists |
| `RAG_SAMPLE_DIR` | `backend/data/samples` | Sample markdown |
| `RAG_INDEX_PATH` | `backend/data/index.json` | Persisted index |
| `RAG_FRONTEND_DIST` | `rag/frontend/dist` | Built UI served by FastAPI when present |
| `RAG_CHUNK_SIZE` / `RAG_CHUNK_OVERLAP` | `420` / `80` | Chunker |
| `RAG_TOP_K` | `4` | Retrieved chunks |

Copy `rag/.env.example` when using Compose.

## Docker deploy

All-in-one image: frontend production build + FastAPI on port **8080**.

```bash
cd rag
docker compose up --build
```

- App: [http://127.0.0.1:8080](http://127.0.0.1:8080)
- Health: [http://127.0.0.1:8080/api/health](http://127.0.0.1:8080/api/health)

Optional LLM: copy `rag/.env.example` to `rag/.env` and set `OPENAI_API_KEY` there (do not paste keys into chat). Compose reads that file if present:

```bash
docker compose --env-file .env up --build
```

The index is stored in the `rag-index` volume. Load samples from the UI (or `POST /api/ingest/samples`) after the stack is up.

### Docker Desktop on Windows

Use the **Containers** view (not MCP Toolkit). From PowerShell, on branch `cursor/rag-from-scratch-77b1`:

```powershell
cd path\to\argocd
git checkout cursor/rag-from-scratch-77b1
cd rag
docker compose up --build
```

Open http://127.0.0.1:8080 on that PC, click **Load sample documents**, then **Run query**. Kubernetes nodes in Docker Desktop are not required for this compose path.

## API map

| Method | Path | Role |
|---|---|---|
| GET | `/api/health` | Liveness |
| GET | `/api/status` | Index size, embedder, generator mode |
| GET | `/api/documents` | Indexed files |
| POST | `/api/ingest/samples` | Chunk + embed bundled corpus |
| POST | `/api/ingest/upload` | Multipart `.txt` / `.md` |
| POST | `/api/query` | `{ "question", "top_k"? }` |
| DELETE | `/api/index` | Reset |

Query responses include `answer`, `generator`, `chunks` (source + score + text), and `pipeline` timings for retrieve/generate.
