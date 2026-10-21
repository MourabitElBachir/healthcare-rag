"""Tiny retrieval evaluation: hit@k on answerable questions, refusal accuracy otherwise.

Each line of the JSONL file is
{"question": str, "expected_source": str | null, "lang": "fr" | "en" (optional, default "fr")}.
``expected_source`` may also be a list (any of them counts as a hit).
``expected_source: null`` means the system should refuse (off-topic question).
``lang`` is the language of the question; metrics are also reported per language.
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
    expected_source: str | tuple[str, ...] | None
    lang: str = "fr"

    @property
    def expected(self) -> tuple[str, ...]:
        if self.expected_source is None:
            return ()
        if isinstance(self.expected_source, str):
            return (self.expected_source,)
        return tuple(self.expected_source)

    @property
    def expected_label(self) -> str:
        return " or ".join(self.expected) or "(refusal)"

    @property
    def cross_lingual(self) -> bool:
        """True when no expected source is in the question's language."""
        from .sources import source_language
        langs = {source_language(s) for s in self.expected}
        return bool(langs) and self.lang not in langs


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
        return any(s in self.cited_sources for s in self.item.expected)


def load_items(path: str | Path) -> list[EvalItem]:
    items = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            expected = row.get("expected_source")
            if isinstance(expected, list):
                expected = tuple(expected)
            items.append(EvalItem(row["question"], expected,
                                  row.get("lang", "fr")))
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


def metrics_by_language(results: list[EvalResult]) -> dict[str, dict]:
    """compute_metrics for each question language, plus "all"."""
    langs = sorted({r.item.lang for r in results})
    out = {lang: compute_metrics([r for r in results if r.item.lang == lang])
           for lang in langs}
    cross = [r for r in results if r.item.cross_lingual]
    if cross:
        out["cross-lingual"] = compute_metrics(cross)
    out["all"] = compute_metrics(results)
    return out


def run_eval(path: str | Path, *, k: int | None = None, embedder: str | None = None,
             config: Config | None = None) -> tuple[list[EvalResult], dict]:
    config = config or Config.from_env()
    encoder, store = load_components(embedder, config)
    results = []
    for item in load_items(path):
        answer = answer_question(item.question, encoder, store, k=k, config=config)
        results.append(EvalResult(item, [p.source for p in answer.citations]))
    return results, compute_metrics(results)
