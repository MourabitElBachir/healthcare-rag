"""Wire configurable local ingestion and extractive question answering."""
from pathlib import Path
from .answer import Answer, ExtractiveAnswerer
from .config import Config
from .embeddings import (EMBEDDERS, Embedder, OnnxEmbedder, HashingEmbedder,
                         SentenceTransformerEmbedder, default_embedder)
from .ingestion import ingest_directory
from .retrieval import Retriever
from .vector_store import ChromaVectorStore


def _components(config: Config, name: str | None, reset: bool = False
                ) -> tuple[Embedder, ChromaVectorStore]:
    name = name or default_embedder()
    if name not in EMBEDDERS:
        raise ValueError(f"embedder must be one of {', '.join(EMBEDDERS)}")
    embedder: Embedder
    if name == "hashing":
        embedder = HashingEmbedder()
    elif name == "st":
        embedder = SentenceTransformerEmbedder(config.model_name)
    else:
        embedder = OnnxEmbedder(config.model_name)
    if reset:
        # Reset must also work when switching embedding models/dimensions.
        import chromadb
        from chromadb.config import Settings
        client = chromadb.PersistentClient(path=str(config.persist_dir),
                                          settings=Settings(anonymized_telemetry=False))
        if config.collection_name in [c.name for c in client.list_collections()]:
            client.delete_collection(config.collection_name)
    return embedder, ChromaVectorStore(config.persist_dir, config.collection_name,
                                      embedder.identity)


def build_index(data_dir: str | Path = "data/sample", *, reset: bool = False,
                embedder: str | None = None, config: Config | None = None) -> int:
    """Index a curated corpus; reset removes stale chunks from earlier versions."""
    config = config or Config.from_env()
    chunks = ingest_directory(data_dir, config.chunk_size, config.overlap)
    encoder, store = _components(config, embedder, reset)
    for start in range(0, len(chunks), 128):
        batch = chunks[start:start + 128]
        store.upsert(batch, encoder.embed([c.text for c in batch]))
    return len(chunks)


def load_components(embedder: str | None = None, config: Config | None = None
                    ) -> tuple[Embedder, ChromaVectorStore]:
    """Create the embedder and store once; reuse them across questions (UI, eval)."""
    return _components(config or Config.from_env(), embedder)


def answer_question(question: str, encoder: Embedder, store: ChromaVectorStore, *,
                    k: int | None = None, config: Config | None = None) -> Answer:
    """Retrieve, filter and answer with already-loaded components."""
    config = config or Config.from_env()
    passages = Retriever(encoder, store).retrieve(question, config.top_k if k is None else k)
    return ExtractiveAnswerer(config.min_score, config.score_margin).answer(question, passages)


def ask(question: str, *, k: int | None = None, embedder: str | None = None,
        config: Config | None = None) -> Answer:
    """Retrieve local evidence and return exact excerpts with citations."""
    config = config or Config.from_env()
    encoder, store = _components(config, embedder)
    return answer_question(question, encoder, store, k=k, config=config)
