from __future__ import annotations

import os
from pathlib import Path


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_embed_model: str = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
    embed_backend: str = os.getenv("EMBED_BACKEND", "auto").strip().lower()
    data_dir: Path = Path(os.getenv("RAG_DATA_DIR", str(Path(__file__).resolve().parents[1] / "data")))
    sample_dir: Path = Path(os.getenv("RAG_SAMPLE_DIR", str(data_dir / "samples")))
    index_path: Path = Path(os.getenv("RAG_INDEX_PATH", str(data_dir / "index.json")))
    chunk_size: int = int(os.getenv("RAG_CHUNK_SIZE", "420"))
    chunk_overlap: int = int(os.getenv("RAG_CHUNK_OVERLAP", "80"))
    top_k: int = int(os.getenv("RAG_TOP_K", "4"))
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")
    force_mock_generator: bool = _env_bool("RAG_FORCE_MOCK", False)

    @property
    def use_openai_embeddings(self) -> bool:
        if self.embed_backend in {"tfidf", "local"}:
            return False
        if self.embed_backend in {"openai"}:
            return bool(self.openai_api_key)
        return bool(self.openai_api_key)

    @property
    def use_openai_generator(self) -> bool:
        if self.force_mock_generator:
            return False
        return bool(self.openai_api_key)

    @property
    def generator_mode(self) -> str:
        return "openai" if self.use_openai_generator else "mock"

    @property
    def embedder_mode(self) -> str:
        return "openai" if self.use_openai_embeddings else "tfidf"


settings = Settings()
