"""Index layer — markdown folder to SQLite FTS5, idempotent by mtime+size."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    path   TEXT PRIMARY KEY,
    mtime  REAL NOT NULL,
    size   INTEGER NOT NULL,
    title  TEXT NOT NULL DEFAULT ''
);
CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
    path UNINDEXED,
    title,
    content,
    tokenize = 'unicode61'
);
"""


class IndexError_(RuntimeError):
    """Indexing failed loudly — empty folder, unreadable file, missing schema."""


@dataclass(frozen=True)
class IndexStats:
    added: int
    updated: int
    removed: int
    unchanged: int

    @property
    def total(self) -> int:
        return self.added + self.updated + self.removed + self.unchanged

    def __str__(self) -> str:  # pragma: no cover - trivial
        return (f"added={self.added} updated={self.updated} "
                f"removed={self.removed} unchanged={self.unchanged}")


def connect(db_path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def _title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or fallback
        if stripped:
            return stripped[:80]
    return fallback


def build_index(folder: Path | str, db_path: Path | str) -> IndexStats:
    root = Path(folder).expanduser()
    if not root.is_dir():
        raise IndexError_(f"folder not found: {root}")
    files = sorted(p for p in root.rglob("*.md") if p.is_file())
    if not files:
        raise IndexError_(f"no markdown files under {root}")

    conn = connect(db_path)
    added = updated = unchanged = 0
    seen: set[str] = set()
    try:
        for path in files:
            key = str(path.resolve())
            seen.add(key)
            stat = path.stat()
            row = conn.execute("SELECT mtime, size FROM documents WHERE path = ?", (key,)).fetchone()
            if row and row[0] == stat.st_mtime and row[1] == stat.st_size:
                unchanged += 1
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                raise IndexError_(f"cannot read {path}: {exc}") from exc
            title = _title(text, path.stem)
            conn.execute("DELETE FROM notes_fts WHERE path = ?", (key,))
            conn.execute(
                "INSERT INTO notes_fts (path, title, content) VALUES (?, ?, ?)", (key, title, text)
            )
            conn.execute(
                "INSERT INTO documents (path, mtime, size, title) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(path) DO UPDATE SET mtime = excluded.mtime, size = excluded.size, "
                "title = excluded.title",
                (key, stat.st_mtime, stat.st_size, title),
            )
            if row:
                updated += 1
            else:
                added += 1
        stale = [r[0] for r in conn.execute("SELECT path FROM documents").fetchall() if r[0] not in seen]
        for key in stale:
            conn.execute("DELETE FROM notes_fts WHERE path = ?", (key,))
            conn.execute("DELETE FROM documents WHERE path = ?", (key,))
        conn.commit()
    finally:
        conn.close()
    return IndexStats(added=added, updated=updated, removed=len(stale), unchanged=unchanged)


def document_count(db_path: Path | str) -> int:
    conn = connect(db_path)
    try:
        return conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    finally:
        conn.close()
