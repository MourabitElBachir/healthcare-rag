"""Persistent Chroma storage with explicit embeddings and cosine scores."""
from dataclasses import dataclass
import chromadb
from chromadb.config import Settings
from .ingestion import Chunk


@dataclass(frozen=True)
class Passage:
    text: str
    source: str
    page: int
    chunk_index: int
    score: float


class ChromaVectorStore:
    def __init__(self, persist_dir: str, collection_name: str = "healthcare_rag",
                 embedding_id: str = "hashing-v1:512"):
        self.client = chromadb.PersistentClient(
            path=str(persist_dir), settings=Settings(anonymized_telemetry=False))
        self.collection_name = collection_name
        self.embedding_id = embedding_id
        self.collection = self.client.get_or_create_collection(
            name=collection_name, embedding_function=None,
            metadata={"hnsw:space": "cosine", "embedding_id": embedding_id})
        if (self.collection.metadata or {}).get("embedding_id") != embedding_id:
            raise ValueError("Embedding provider changed; use ingest --reset")

    def reset(self) -> None:
        """Delete only this collection, leaving other collections intact."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name, embedding_function=None,
            metadata={"hnsw:space": "cosine", "embedding_id": self.embedding_id})

    def upsert(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("One embedding is required per chunk")
        # Stay below Chroma's insertion batch limits for small local corpora.
        for start in range(0, len(chunks), 128):
            batch = chunks[start:start + 128]
            self.collection.upsert(
                ids=[c.id for c in batch], documents=[c.text for c in batch],
                embeddings=embeddings[start:start + 128],
                metadatas=[{"source": c.source, "page": c.page,
                            "chunk_index": c.chunk_index} for c in batch])

    def query(self, embedding: list[float], k: int = 4) -> list[Passage]:
        if k < 1:
            raise ValueError("k must be positive")
        count = self.collection.count()
        if not count:
            return []
        results = self.collection.query(query_embeddings=[embedding],
                                        n_results=min(k, count),
                                        include=["documents", "metadatas", "distances"])
        return [Passage(text, meta["source"], int(meta["page"]),
                        int(meta["chunk_index"]), 1.0 - float(distance))
                for text, meta, distance in zip(results["documents"][0],
                                                results["metadatas"][0],
                                                results["distances"][0])]
