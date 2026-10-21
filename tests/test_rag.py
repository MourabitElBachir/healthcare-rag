"""Offline coverage: no sentence-transformer model is loaded."""
from pathlib import Path
import pytest
from healthcare_rag.answer import ExtractiveAnswerer, LLMAnswerer
from healthcare_rag.config import Config
from healthcare_rag.embeddings import HashingEmbedder
from healthcare_rag.ingestion import chunk_text, ingest_directory, load_pages
from healthcare_rag.pipeline import ask, build_index
from healthcare_rag.retrieval import Retriever
from healthcare_rag.vector_store import ChromaVectorStore, Passage

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "sample"


def test_chunk_overlap_metadata_and_stability():
    chunks = chunk_text("abcdefghijklmnop", "guide.txt", 2, 8, 3)
    assert [c.text for c in chunks] == ["abcdefgh", "fghijklm", "klmnop"]
    assert chunks[0].text[-3:] == chunks[1].text[:3]
    assert [(c.source, c.page, c.chunk_index) for c in chunks] == [
        ("guide.txt", 2, i) for i in range(3)]
    assert chunks == chunk_text("abcdefghijklmnop", "guide.txt", 2, 8, 3)
    assert len({c.id for c in chunks}) == 3
    with pytest.raises(ValueError):
        chunk_text("hello", "x", chunk_size=3, overlap=3)
    assert chunk_text("", "empty") == []


def test_text_pages(tmp_path):
    path = tmp_path / "guide.md"
    path.write_text("first\fsecond", encoding="utf-8")
    assert list(load_pages(path)) == [(1, "first"), (2, "second")]
    assert [c.page for c in ingest_directory(tmp_path)] == [1, 2]


def test_samples():
    chunks = ingest_directory(SAMPLES)
    assert {c.source for c in chunks} == {
        "hand_hygiene.txt", "paracetamol.txt", "flu_vaccination.txt"}
    assert all(c.page == 1 and len(c.text) <= 800 for c in chunks)
    for path in SAMPLES.glob("*.txt"):
        assert 300 <= len(path.read_text().split()) <= 600


def test_end_to_end(tmp_path):
    config = Config(persist_dir=str(tmp_path / "index"), min_score=0.0)
    count = build_index(SAMPLES, embedder="hashing", config=config)
    assert count > 3
    assert build_index(SAMPLES, embedder="hashing", config=config) == count
    store = ChromaVectorStore(config.persist_dir)
    assert store.collection.count() == count
    passages = Retriever(HashingEmbedder(), store).retrieve("hand hygiene", 4)
    assert passages and passages[0].source == "hand_hygiene.txt"
    assert all(p.page == 1 and p.chunk_index >= 0 for p in passages)
    result = ask("hand hygiene", embedder="hashing", config=config)
    assert result.citations
    for i, passage in enumerate(result.citations, 1):
        assert f"[{i}] {passage.source} p.{passage.page}, chunk {passage.chunk_index}" in result.text
        assert passage.text in result.text
    build_index(SAMPLES, reset=True, embedder="hashing", config=config)
    assert ChromaVectorStore(config.persist_dir).collection.count() == count


def test_refusal_empty_and_irrelevant(tmp_path):
    config = Config(persist_dir=str(tmp_path / "empty"))
    assert not ask("hand hygiene", embedder="hashing", config=config).citations
    result = ExtractiveAnswerer().answer("orbital mechanics", [
        Passage("Wash hands", "guide.txt", 1, 0, 0.01)])
    assert not result.citations and "cannot answer" in result.text
    encoder = HashingEmbedder()
    store = ChromaVectorStore(str(tmp_path / "irrelevant"))
    chunks = chunk_text("hand hygiene soap water", "guide.txt")
    store.upsert(chunks, encoder.embed([c.text for c in chunks]))
    passages = Retriever(encoder, store).retrieve("astronomy galaxies telescope", 4)
    assert not ExtractiveAnswerer().answer("astronomy galaxies telescope", passages).citations


def test_embedding_guard_and_stub(tmp_path):
    ChromaVectorStore(str(tmp_path), embedding_id="hashing-v1:512")
    with pytest.raises(ValueError, match="Embedding provider changed"):
        ChromaVectorStore(str(tmp_path), embedding_id="different")
    with pytest.raises(NotImplementedError):
        LLMAnswerer().answer("question", [])


def test_sources_metadata_file_is_not_ingested(tmp_path):
    (tmp_path / "SOURCES.md").write_text("provenance table", encoding="utf-8")
    (tmp_path / "doc.txt").write_text("hand hygiene", encoding="utf-8")
    assert {c.source for c in ingest_directory(tmp_path)} == {"doc.txt"}
