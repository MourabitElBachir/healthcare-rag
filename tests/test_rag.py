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


def test_relevance_filter_floor_and_margin():
    passages = [Passage("a", "a.txt", 1, 0, 0.75), Passage("b", "b.txt", 1, 0, 0.72),
                Passage("c", "c.pdf", 9, 3, 0.65), Passage("d", "d.txt", 1, 0, 0.40)]
    kept = ExtractiveAnswerer(min_score=0.6, score_margin=0.08).select(passages)
    assert [p.source for p in kept] == ["a.txt", "b.txt"]  # c: outside margin, d: below floor
    assert [p.source for p in ExtractiveAnswerer(0.6, 0.2).select(passages)] == [
        "a.txt", "b.txt", "c.pdf"]
    assert ExtractiveAnswerer(0.8, 0.08).select(passages) == []
    config = Config()
    assert (config.min_score, config.score_margin) == (0.6, 0.08)


def test_eval_metrics_and_loader(tmp_path):
    from healthcare_rag.evaluation import EvalItem, EvalResult, compute_metrics, load_items
    results = [
        EvalResult(EvalItem("q1", "a.txt"), ["a.txt", "b.txt"]),  # hit
        EvalResult(EvalItem("q2", "a.txt"), ["b.txt"]),           # miss
        EvalResult(EvalItem("q3", "c.pdf"), []),                  # false refusal
        EvalResult(EvalItem("off1", None), []),                   # correct refusal
        EvalResult(EvalItem("off2", None), ["a.txt"]),            # wrongly answered
    ]
    m = compute_metrics(results)
    assert (m["hits"], m["answerable"], m["false_refusals"]) == (1, 3, 1)
    assert abs(m["hit_at_k"] - 1 / 3) < 1e-9
    assert (m["correct_refusals"], m["off_topic"], m["refusal_accuracy"]) == (1, 2, 0.5)
    path = tmp_path / "q.jsonl"
    path.write_text('{"question": "x", "expected_source": "a.txt"}\n\n'
                    '{"question": "y", "expected_source": null}\n', encoding="utf-8")
    assert load_items(path) == [EvalItem("x", "a.txt"), EvalItem("y", None)]


def test_eval_end_to_end_with_hashing(tmp_path):
    from healthcare_rag.evaluation import run_eval
    config = Config(persist_dir=str(tmp_path / "index"), min_score=0.0)
    build_index(SAMPLES, embedder="hashing", config=config)
    path = tmp_path / "q.jsonl"
    path.write_text('{"question": "hand hygiene soap", "expected_source": "hand_hygiene.txt"}\n',
                    encoding="utf-8")
    results, metrics = run_eval(path, embedder="hashing", config=config)
    assert len(results) == 1 and metrics["hits"] == 1


def test_clean_pdf_text():
    from healthcare_rag.ingestion import clean_pdf_text
    assert clean_pdf_text("Elles contr i-\nbuent à") == "Elles contribuent à"
    assert clean_pdf_text("néces-\nsite") == "nécessite"
    assert clean_pdf_text("hygiéno -diététiques") == "hygiéno-diététiques"
    assert clean_pdf_text("IEC-\nARA2 et\nsuite") == "IEC-\nARA2 et\nsuite"


def test_streamlit_app_answers_and_refuses(tmp_path, monkeypatch):
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest
    config = Config(persist_dir=str(tmp_path / "index"))
    build_index(SAMPLES, embedder="hashing", config=config)
    monkeypatch.setenv("HEALTHCARE_RAG_PERSIST_DIR", config.persist_dir)
    monkeypatch.setenv("HEALTHCARE_RAG_EMBEDDER", "hashing")
    monkeypatch.setenv("HEALTHCARE_RAG_MIN_SCORE", "0.0")
    app_path = Path(__file__).resolve().parents[1] / "src" / "healthcare_rag" / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=60).run()
    assert not at.exception
    at.text_input[0].input("hand hygiene soap water").run()
    assert not at.exception and at.success
    assert any("hand_hygiene.txt" in m.value for m in at.markdown)
    monkeypatch.setenv("HEALTHCARE_RAG_MIN_SCORE", "0.99")
    at = AppTest.from_file(str(app_path), default_timeout=60).run()
    at.text_input[0].input("astronomy telescope").run()
    assert at.error and "Je ne peux pas" in at.error[0].value


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    persist = str(tmp_path / "index")
    build_index(SAMPLES, embedder="hashing", config=Config(persist_dir=persist))
    monkeypatch.setenv("HEALTHCARE_RAG_PERSIST_DIR", persist)
    monkeypatch.setenv("HEALTHCARE_RAG_EMBEDDER", "hashing")
    monkeypatch.setenv("HEALTHCARE_RAG_MIN_SCORE", "0.0")
    from healthcare_rag import api
    api.get_components.cache_clear()
    with TestClient(api.app) as client:
        yield client, monkeypatch
    api.get_components.cache_clear()


def test_api_health_and_sources(api_client):
    client, _ = api_client
    health = client.get("/api/health").json()
    assert health["status"] == "ok" and health["chunks"] > 3 and health["embedder"] == "hashing"
    sources = client.get("/api/sources").json()
    assert len(sources) == 4 and all(s["url"].startswith("https://") for s in sources)


def test_api_ask_answers_and_refuses(api_client):
    client, monkeypatch = api_client
    body = client.post("/api/ask", json={"question": "hand hygiene soap water", "k": 3}).json()
    assert not body["refused"] and body["k"] == 3
    first = body["citations"][0]
    assert first["source"] == "hand_hygiene.txt" and first["rank"] == 1
    assert {"page", "chunk_index", "score", "text", "url"} <= first.keys()
    monkeypatch.setenv("HEALTHCARE_RAG_MIN_SCORE", "0.99")
    refused = client.post("/api/ask", json={"question": "astronomy telescope"}).json()
    assert refused["refused"] and not refused["citations"]
    assert "Je ne peux pas" in refused["message"]["fr"]
    assert client.post("/api/ask", json={"question": ""}).status_code == 422
    assert client.post("/api/ask", json={"question": "x", "k": 50}).status_code == 422
