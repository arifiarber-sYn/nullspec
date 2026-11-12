"""diary-index — local full-text search over a folder of markdown journals."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from index import IndexError_, build_index, document_count
from search import search

DEFAULT_DB = Path.home() / ".local" / "share" / "diary-index" / "diary.db"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="diary-index", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    index_cmd = sub.add_parser("index", help="(re)index a markdown folder")
    index_cmd.add_argument("folder", nargs="?", default=".", help="folder to crawl (recursive)")
    index_cmd.add_argument("--db", default=str(DEFAULT_DB))

    search_cmd = sub.add_parser("search", help="query the index")
    search_cmd.add_argument("term")
    search_cmd.add_argument("--db", default=str(DEFAULT_DB))
    search_cmd.add_argument("--limit", type=int, default=10)

    stats_cmd = sub.add_parser("stats", help="document count")
    stats_cmd.add_argument("--db", default=str(DEFAULT_DB))

    args = parser.parse_args(argv)
    db = Path(args.db).expanduser()
    db.parent.mkdir(parents=True, exist_ok=True)

    try:
        if args.command == "index":
            stats = build_index(args.folder, db)
            print(f"indexed {stats.total} files: {stats}")
            return 0
        if args.command == "stats":
            print(f"{document_count(db)} documents in {db}")
            return 0
        results = search(db, args.term, args.limit)
    except IndexError_ as exc:
        print(f"diary-index: {exc}", file=sys.stderr)
        return 1

    if not results:
        print(f"no matches for {args.term!r}", file=sys.stderr)
        return 1
    for hit in results:
        print(f"{hit.title or Path(hit.path).name}  ({hit.path})")
        print(f"    {hit.snippet.strip()}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
