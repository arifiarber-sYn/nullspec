"""Search layer — FTS5 match with snippet context."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from index import IndexError_, connect


@dataclass(frozen=True)
class SearchResult:
    path: str
    title: str
    snippet: str
    rank: float


def _safe_query(term: str) -> str:
    """Quote each token so user input can never break FTS5 syntax."""
    tokens = re.findall(r"\w+", term, flags=re.UNICODE)
    if not tokens:
        raise IndexError_("search term has no searchable words")
    return " ".join(f'"{token}"' for token in tokens)


def search(db_path: Path | str, term: str, limit: int = 10) -> list[SearchResult]:
    db = Path(db_path)
    if not db.exists():
        raise IndexError_(f"index not found: {db}")
    conn = connect(db)
    try:
        rows = conn.execute(
            "SELECT path, title, snippet(notes_fts, 2, '[', ']', ' … ', 12), rank "
            "FROM notes_fts WHERE notes_fts MATCH ? ORDER BY rank LIMIT ?",
            (_safe_query(term), int(limit)),
        ).fetchall()
    except sqlite3.OperationalError as exc:
        raise IndexError_(f"query failed: {exc}") from exc
    finally:
        conn.close()
    return [SearchResult(path=r[0], title=r[1], snippet=r[2], rank=r[3]) for r in rows]
