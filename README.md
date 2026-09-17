# This repository

GitOps sample trees (`gitops-argocd`, `pod-metadata-master`) plus **NovaRAG**, a from-scratch RAG app.

Start here for RAG: [`rag/README.md`](rag/README.md)

```bash
cd rag/backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pytest -q
uvicorn app.main:app --reload --port 8000
```
