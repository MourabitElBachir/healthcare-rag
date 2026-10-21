"""Tiny retrieval evaluation: hit@k on answerable questions, refusal accuracy otherwise.

Each line of the JSONL file is {"question": str, "expected_source": str | null}.
``expected_source: null`` means the system should refuse (off-topic question).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .config import Config
from .pipeline import answer_question, load_components


@dataclass(frozen=True)
class EvalItem:
    question: str
    expected_source: str | None


@dataclass(frozen=True)
class EvalResult:
    item: EvalItem
    cited_sources: list[str]  # sources of the cited passages, in rank order

    @property
    def refused(self) -> bool:
        return not self.cited_sources

    @property
    def correct(self) -> bool:
        if self.item.expected_source is None:
            return self.refused
        return self.item.expected_source in self.cited_sources


def load_items(path: str | Path) -> list[EvalItem]:
    items = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            items.append(EvalItem(row["question"], row.get("expected_source")))
    return items


def compute_metrics(results: list[EvalResult]) -> dict[str, float | int]:
    """hit@k = share of answerable questions whose expected source is cited;
    refusal_accuracy = share of off-topic questions that were refused;
    false_refusals = answerable questions that got no citation."""
    answerable = [r for r in results if r.item.expected_source is not None]
    off_topic = [r for r in results if r.item.expected_source is None]
    hits = sum(r.correct for r in answerable)
    refusals = sum(r.correct for r in off_topic)
    return {
        "answerable": len(answerable), "hits": hits,
        "hit_at_k": hits / len(answerable) if answerable else 0.0,
        "off_topic": len(off_topic), "correct_refusals": refusals,
        "refusal_accuracy": refusals / len(off_topic) if off_topic else 0.0,
        "false_refusals": sum(r.refused for r in answerable),
    }


def run_eval(path: str | Path, *, k: int | None = None, embedder: str | None = None,
             config: Config | None = None) -> tuple[list[EvalResult], dict]:
    config = config or Config.from_env()
    encoder, store = load_components(embedder, config)
    results = []
    for item in load_items(path):
        answer = answer_question(item.question, encoder, store, k=k, config=config)
        results.append(EvalResult(item, [p.source for p in answer.citations]))
    return results, compute_metrics(results)
