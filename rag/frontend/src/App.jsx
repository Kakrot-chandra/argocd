import { useCallback, useEffect, useMemo, useState } from "react";

const STAGES = ["ingest", "chunk", "embed", "index", "retrieve", "generate"];

async function api(path, options) {
  const response = await fetch(path, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.detail || response.statusText);
  }
  return body;
}

export default function App() {
  const [status, setStatus] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [question, setQuestion] = useState("How often should I descale the NovaBrew carafe?");
  const [result, setResult] = useState(null);
  const [pipeline, setPipeline] = useState([]);
  const [busy, setBusy] = useState(null);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    const [nextStatus, docs] = await Promise.all([api("/api/status"), api("/api/documents")]);
    setStatus(nextStatus);
    setDocuments(docs.documents || []);
  }, []);

  useEffect(() => {
    refresh().catch((err) => setError(err.message));
  }, [refresh]);

  const seenStages = useMemo(() => new Set(pipeline.map((s) => s.stage)), [pipeline]);

  async function loadSamples() {
    setBusy("samples");
    setError("");
    try {
      const body = await api("/api/ingest/samples", { method: "POST" });
      setPipeline(body.pipeline || []);
      setResult(null);
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(null);
    }
  }

  async function onUpload(event) {
    const files = event.target.files;
    if (!files?.length) return;
    const data = new FormData();
    for (const file of files) data.append("files", file);
    setBusy("upload");
    setError("");
    try {
      const body = await api("/api/ingest/upload", { method: "POST", body: data });
      setPipeline(body.pipeline || []);
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(null);
      event.target.value = "";
    }
  }

  async function ask(event) {
    event.preventDefault();
    setBusy("query");
    setError("");
    try {
      const body = await api("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      setResult(body);
      setPipeline((prev) => {
        const ingest = prev.filter((s) => ["ingest", "chunk", "embed", "index"].includes(s.stage));
        return [...ingest, ...(body.pipeline || [])];
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(null);
    }
  }

  async function resetIndex() {
    setBusy("reset");
    try {
      await api("/api/index", { method: "DELETE" });
      setResult(null);
      setPipeline([]);
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="shell">
      <header className="hero">
        <p className="kicker">From-scratch RAG lab</p>
        <h1>NovaRAG</h1>
        <p className="lede">
          Ingest a tiny multi-topic corpus, watch chunking and retrieval, then generate an answer.
          Works offline with a mock generator; set <code>OPENAI_API_KEY</code> for a real model.
        </p>
        <dl className="meta">
          <div>
            <dt>Index</dt>
            <dd>{status?.ready ? `${status.chunk_count} chunks / ${status.document_count} docs` : "empty"}</dd>
          </div>
          <div>
            <dt>Embedder</dt>
            <dd>{status?.embedder || "—"}</dd>
          </div>
          <div>
            <dt>Generator</dt>
            <dd>{status?.generator || "—"}</dd>
          </div>
        </dl>
      </header>

      <ol className="pipeline">
        {STAGES.map((name) => {
          const hit = pipeline.find((s) => s.stage === name);
          return (
            <li key={name} className={hit ? "on" : seenStages.size && name === "index" ? "" : ""}>
              <span className="stage-name">{name}</span>
              <span className="stage-ms">{hit ? `${hit.ms} ms` : "idle"}</span>
            </li>
          );
        })}
      </ol>

      <main className="grid">
        <section className="panel">
          <h2>Corpus</h2>
          <p className="hint">Five bundled topics: coffee FAQ, remote policy, irrigation how-to, bees, kitchari.</p>
          <div className="row">
            <button type="button" onClick={loadSamples} disabled={!!busy}>
              {busy === "samples" ? "Indexing…" : "Load sample documents"}
            </button>
            <label className="file">
              Upload .txt / .md
              <input type="file" accept=".txt,.md" multiple onChange={onUpload} />
            </label>
            <button type="button" className="ghost" onClick={resetIndex} disabled={!!busy}>
              Clear index
            </button>
          </div>
          <ul className="docs">
            {documents.length === 0 && <li className="muted">No documents indexed yet.</li>}
            {documents.map((doc) => (
              <li key={doc.id}>
                <strong>{doc.name}</strong>
                <span>
                  {doc.topic} · {doc.source} · {doc.chars} chars
                </span>
              </li>
            ))}
          </ul>
        </section>

        <section className="panel">
          <h2>Ask</h2>
          <form onSubmit={ask}>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={4}
              placeholder="Ask something that should hit only one topic…"
            />
            <button type="submit" disabled={!!busy || !status?.ready}>
              {busy === "query" ? "Retrieving…" : "Run query"}
            </button>
          </form>
          {error && <p className="error">{error}</p>}
          {result && (
            <article className="answer">
              <header>
                <h3>Answer</h3>
                <span className="pill">{result.generator}</span>
              </header>
              <pre>{result.answer}</pre>
            </article>
          )}
        </section>
      </main>

      {result?.chunks && (
        <section className="panel chunks">
          <h2>Retrieved chunks</h2>
          <div className="cards">
            {result.chunks.map((chunk) => (
              <article key={chunk.id}>
                <header>
                  <strong>{chunk.source}</strong>
                  <span>#{chunk.index}</span>
                  <span className="score">{chunk.score.toFixed(3)}</span>
                </header>
                <div className="bar">
                  <i style={{ width: `${Math.max(8, chunk.score * 100)}%` }} />
                </div>
                <p>{chunk.text}</p>
              </article>
            ))}
          </div>
        </section>
      )}

      <footer>
        <p>Pipeline: ingest → chunk → embed → index → retrieve → generate. Sample queries work best after loading bundled docs.</p>
      </footer>
    </div>
  );
}
