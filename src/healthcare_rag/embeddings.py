"""Explicit embedding providers; hashing never downloads a model."""
from hashlib import sha256
from math import sqrt
import re
from typing import Protocol


class Embedder(Protocol):
    @property
    def identity(self) -> str: ...

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class SentenceTransformerEmbedder:
    """Load sentence-transformers only when embeddings are requested."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None

    @property
    def identity(self) -> str:
        return f"st:{self.model_name}"

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model.encode(texts, normalize_embeddings=True).tolist()


class HashingEmbedder:
    """Tiny normalized signed bag-of-words baseline; no semantic understanding."""

    def __init__(self, dimensions: int = 512):
        if dimensions < 1:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions

    @property
    def identity(self) -> str:
        return f"hashing-v1:{self.dimensions}"

    def embed(self, texts: list[str]) -> list[list[float]]:
        result = []
        for text in texts:
            vector = [0.0] * self.dimensions
            for token in re.findall(r"\w+", text.casefold()):
                digest = sha256(token.encode()).digest()
                vector[int.from_bytes(digest[:8], "big") % self.dimensions] += (
                    1.0 if digest[8] % 2 else -1.0)
            norm = sqrt(sum(value * value for value in vector)) or 1.0
            result.append([value / norm for value in vector])
        return result
