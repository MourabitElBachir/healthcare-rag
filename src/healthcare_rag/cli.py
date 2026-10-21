"""Command-line ingestion and questions."""
import argparse
from .embeddings import EMBEDDERS
from .pipeline import ask, build_index
from .sources import fetch_all


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embedder", choices=list(EMBEDDERS), default=None,
                        help="default: $HEALTHCARE_RAG_EMBEDDER or onnx")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest")
    ingest.add_argument("--data-dir", default="data/sample")
    ingest.add_argument("--reset", action="store_true")
    fetch = commands.add_parser("fetch", help="download official public sources")
    fetch.add_argument("--out-dir", default="data/public/raw")
    query = commands.add_parser("ask")
    query.add_argument("question")
    query.add_argument("-k", type=int, default=None)
    evaluate = commands.add_parser("eval", help="hit@k and refusal accuracy")
    evaluate.add_argument("--file", default="eval/questions.jsonl")
    evaluate.add_argument("-k", type=int, default=None)
    for command in (ingest, query, evaluate):
        command.add_argument("--embedder", choices=list(EMBEDDERS),
                             default=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if args.command == "fetch":
            results = fetch_all(args.out_dir)
            for source, _, status in results:
                print(f"{source.filename}: {status}")
            if any(path is None for _, path, _ in results):
                raise SystemExit(1)
        elif args.command == "ingest":
            print(f"Indexed {build_index(args.data_dir, reset=args.reset, embedder=args.embedder)} chunks.")
        elif args.command == "eval":
            from .evaluation import run_eval
            results, _ = run_eval(args.file, k=args.k, embedder=args.embedder)
            for r in results:
                status = "OK  " if r.correct else "MISS"
                got = ", ".join(dict.fromkeys(r.cited_sources)) or "(refused)"
                print(f"{status} [{r.item.lang}] {r.item.question}\n     expected: "
                      f"{r.item.expected_label} | got: {got}")
            from .evaluation import metrics_by_language
            print()
            for lang, m in metrics_by_language(results).items():
                print(f"[{lang.upper():>3}] hit@k: {m['hits']}/{m['answerable']} = {m['hit_at_k']:.2f}"
                      f" | false refusals: {m['false_refusals']}"
                      + (f" | refusal accuracy: {m['correct_refusals']}/{m['off_topic']}"
                         f" = {m['refusal_accuracy']:.2f}" if m['off_topic'] else ""))
        else:
            print(ask(args.question, k=args.k, embedder=args.embedder).text)
    except ValueError as exc:
        parser.error(str(exc))
