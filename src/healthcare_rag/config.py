"""Environment-overridable configuration (HEALTHCARE_RAG_*)."""
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Config:
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    persist_dir: str = ".chroma"
    collection_name: str = "healthcare_rag"
    chunk_size: int = 800
    overlap: int = 150
    top_k: int = 4
    min_score: float = 0.55
    score_margin: float = 0.08
    max_per_source: int = 2  # top-k diversity cap; 0 disables it

    @classmethod
    def from_env(cls) -> "Config":
        """Read settings on demand, rather than at import time."""
        defaults = cls()
        values = {}
        for name, cast in (("model_name", str), ("persist_dir", str),
                           ("collection_name", str), ("chunk_size", int),
                           ("overlap", int), ("top_k", int), ("min_score", float),
                           ("score_margin", float),
                           ("max_per_source", int)):
            values[name] = cast(os.getenv("HEALTHCARE_RAG_" + name.upper(),
                                         str(getattr(defaults, name))))
        return cls(**values)
