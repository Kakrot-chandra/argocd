from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.pipeline import RagPipeline
from app.store import IndexStore


def test_sample_query_returns_answer_and_chunks(tmp_path: Path, monkeypatch) -> None:
    store = IndexStore(path=tmp_path / "index.json")
    pipe = RagPipeline(store)
    sample_dir = Path(__file__).resolve().parents[1] / "data" / "samples"
    pipe.ingest_paths(sorted(sample_dir.glob("*.md")))

    result = pipe.query("What does error E4 mean on the NovaBrew?", top_k=4)
    assert result["generator"] == "mock"
    assert result["chunks"]
    assert "novabrew" in result["chunks"][0]["source"]
    assert "E4" in result["answer"] or "overheat" in result["answer"].lower() or "heater" in result["answer"].lower()
    stages = [s["stage"] for s in result["pipeline"]]
    assert stages == ["retrieve", "generate"]


def test_health_and_ingest_via_http(tmp_path: Path, monkeypatch) -> None:
    from app import main as mainmod

    store = IndexStore(path=tmp_path / "http-index.json")
    mainmod.store = store
    mainmod.pipeline = RagPipeline(store)
    client = TestClient(app)
    assert client.get("/api/health").json()["ok"] is True
    status = client.get("/api/status").json()
    assert status["ready"] is False
    ingested = client.post("/api/ingest/samples")
    assert ingested.status_code == 200
    body = ingested.json()
    assert body["chunk_count"] > 5
    queried = client.post("/api/query", json={"question": "Tuesday office cadence at Northwind?"})
    assert queried.status_code == 200
    payload = queried.json()
    assert payload["chunks"][0]["source"].startswith("northwind")
    assert "retrieve" in {s["stage"] for s in payload["pipeline"]}
