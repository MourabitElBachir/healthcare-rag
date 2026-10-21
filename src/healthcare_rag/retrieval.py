"""Question embedding and nearest-passage retrieval."""
from .embeddings import Embedder
from .vector_store import ChromaVectorStore, Passage


class Retriever:
    def __init__(self, embedder: Embedder, store: ChromaVectorStore):
        self.embedder = embedder
        self.store = store

    def retrieve(self, question: str, k: int = 4) -> list[Passage]:
        if not question.strip():
            return []
        return self.store.query(self.embedder.embed([question])[0], k)
