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
    def __init__(self, min_score: float = 0.25):
        self.min_score = min_score

    def answer(self, question: str, passages: list[Passage]) -> Answer:
        citations = [p for p in passages if p.score >= self.min_score]
        if not question.strip() or not citations:
            return Answer("I cannot answer from the available source passages. "
                          "Je ne peux pas répondre à partir des sources disponibles.", [])
        text = "\n\n".join(
            f"[{i}] {p.source} p.{p.page}, chunk {p.chunk_index}\n{p.text}"
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
