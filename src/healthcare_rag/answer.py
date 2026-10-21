"""Extractive answers quote stored passages without generating medical claims."""
from dataclasses import dataclass
from typing import Protocol
from .vector_store import Passage


@dataclass(frozen=True)
class Answer:
    text: str
    citations: list[Passage]


class AnswerGenerator(Protocol):
    def answer(self, question: str, passages: list[Passage]) -> Answer: ...


class ExtractiveAnswerer:
    """Return cited passages, keeping only those that are clearly relevant.

    A passage is kept when its cosine score is >= ``min_score`` (absolute floor)
    AND >= ``best_score - score_margin`` (relative margin to the top passage).
    """

    def __init__(self, min_score: float = 0.6, score_margin: float = 0.08):
        self.min_score = min_score
        self.score_margin = score_margin

    def select(self, passages: list[Passage]) -> list[Passage]:
        """Apply the absolute floor and the relative margin filters."""
        kept = [p for p in passages if p.score >= self.min_score]
        if not kept:
            return []
        best = max(p.score for p in kept)
        return [p for p in kept if p.score >= best - self.score_margin]

    def answer(self, question: str, passages: list[Passage]) -> Answer:
        citations = self.select(passages)
        if not question.strip() or not citations:
            return Answer("I cannot answer from the available source passages. "
                          "Je ne peux pas répondre à partir des sources disponibles.", [])
        text = "\n\n".join(
            f"[{i}] {p.source} p.{p.page}, chunk {p.chunk_index} (score {p.score:.2f})\n{p.text}"
            for i, p in enumerate(citations, 1))
        return Answer(text, citations)


class LLMAnswerer:
    """Extension point: call a local LLM (e.g. Ollama) with retrieved passages.

    Implement answer(), constrain generation to supplied evidence, validate every
    citation against that evidence, and refuse unsupported questions. No client,
    model, or network call is implemented here.
    """

    def answer(self, question: str, passages: list[Passage]) -> Answer:
        raise NotImplementedError("Plug in a locally hosted LLM and citation validation")
