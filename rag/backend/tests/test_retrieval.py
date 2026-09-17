from __future__ import annotations

from pathlib import Path

from app.pipeline import RagPipeline
from app.store import IndexStore


def _pipeline(tmp_path: Path) -> RagPipeline:
    store = IndexStore(path=tmp_path / "index.json")
    return RagPipeline(store)


def test_retrieval_ranks_matching_topic_first(tmp_path: Path) -> None:
    pipe = _pipeline(tmp_path)
    sample_dir = Path(__file__).resolve().parents[1] / "data" / "samples"
    pipe.ingest_paths(sorted(sample_dir.glob("*.md")))

    coffee = pipe.retrieve("How often should I descale the NovaBrew carafe?", top_k=3)
    assert coffee, "expected coffee chunks"
    assert "novabrew" in coffee[0]["source"]
    assert coffee[0]["score"] >= coffee[-1]["score"]

    policy = pipe.retrieve("What is the monthly home internet stipend at Northwind Labs?", top_k=3)
    assert "northwind" in policy[0]["source"]

    irrigation = pipe.retrieve("How do I factory reset a HelioFlow 3 controller?", top_k=3)
    assert "helioflow" in irrigation[0]["source"]

    bees = pipe.retrieve("When should I treat Varroa mites in August?", top_k=3)
    assert "honeybee" in bees[0]["source"]

    food = pipe.retrieve("How long do I simmer mung dal kitchari?", top_k=3)
    assert "kitchari" in food[0]["source"]


def test_unrelated_query_does_not_mix_all_topics_as_top_hit(tmp_path: Path) -> None:
    pipe = _pipeline(tmp_path)
    sample_dir = Path(__file__).resolve().parents[1] / "data" / "samples"
    pipe.ingest_paths(sorted(sample_dir.glob("*.md")))
    hits = pipe.retrieve("oxalic acid vapor treatment for mites", top_k=2)
    sources = {h["source"] for h in hits}
    assert "honeybee-colony.md" in sources
    assert "kitchari-recipe.md" not in sources
