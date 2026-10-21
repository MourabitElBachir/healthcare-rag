"""Command-line ingestion and questions."""
import argparse
from .pipeline import ask, build_index
from .sources import fetch_all


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embedder", choices=["hashing", "st"], default="st")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest")
    ingest.add_argument("--data-dir", default="data/sample")
    ingest.add_argument("--reset", action="store_true")
    fetch = commands.add_parser("fetch", help="download official public sources")
    fetch.add_argument("--out-dir", default="data/public/raw")
    query = commands.add_parser("ask")
    query.add_argument("question")
    query.add_argument("-k", type=int, default=None)
    for command in (ingest, query):
        command.add_argument("--embedder", choices=["hashing", "st"],
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
        else:
            print(ask(args.question, k=args.k, embedder=args.embedder).text)
    except ValueError as exc:
        parser.error(str(exc))
