# diary-index

## Requirements

1. The app indexes every `*.md` file under a user-supplied folder into a SQLite database created with the stdlib `sqlite3` module, using an FTS5 virtual table for full-text search.
   - Acceptance: Re-running indexing on an unchanged folder is idempotent (no duplicate rows), and the DB path is configurable via a CLI flag.

2. Each indexed document row stores the file path (relative to the supplied root), the file's mtime, and the full text, so stale rows can be detected and refreshed.
   - Acceptance: Editing a file then re-indexing updates its row's text and mtime; deleting a file removes its row; an unchanged file is not re-inserted.

3. The app provides a search command that runs an FTS5 `MATCH` query against the index and returns ranked results with the matching file path and a context snippet.
   - Acceptance: A search for a term present in one file returns that file ranked first; a search with no matches returns an empty result list, not an error.

4. The app is read-only with respect to the source markdown folder: it reads files and mtimes only, never writes, renames, or deletes markdown files.
   - Acceptance: No code path opens a markdown file in a writable mode or issues filesystem mutations; a test asserts no `os`/`pathlib` write calls against the source tree.

5. An empty folder (no `*.md` files) or a missing/empty index is an error with a non-zero exit code and a clear stderr message, per the "fail loudly" rule.
   - Acceptance: Indexing a folder with zero markdown files exits 1; searching before any index exists exits 1; neither produces silent empty JSON output.

## Design

Modules (all stdlib, one concern each):

- `index.py` — scans the root for `*.md` files via `pathlib.Path.rglob`, compares each file's mtime against the existing `documents` table, and inserts/updates only changed rows. Owns the SQLite schema: an FTS5 virtual table `docs_fts(text, path, mtime UNINDEXED)` plus a `documents(path TEXT PRIMARY KEY, mtime REAL, fts_rowid INTEGER)` mapping table. Exposes `build_index(root: Path, db: Connection) -> IndexStats` returning a frozen `IndexStats(added, updated, removed)` dataclass.

- `search.py` — runs `SELECT path, snippet(docs_fts, 1, ...), rank FROM docs_fts WHERE docs_fts MATCH ? ORDER BY rank` against an open connection and returns a tuple of `SearchResult` frozen dataclasses (`path: str`, `snippet: str`, `rank: float`). Exposes `search(db: Connection, query: str, limit: int) -> tuple[SearchResult, ...]`.

- `cli.py` — the only module that prints human text. Subcommands: `index <root> [--db PATH]` builds the index; `search <query> [--db PATH] [--limit N]` prints ranked results as JSON. Opens/closes the `sqlite3` connection, translates `OperationalError` and empty-index conditions into exit code 1 with a stderr message.

Data records (frozen dataclasses, never bare dicts across module borders): `IndexStats`, `SearchResult`. The SQLite file is the only persistent state; JSON is used for the `search` command's stdout payload. Type hints on every public function; `from __future__ import annotations` at the top of each module.

## Tasks

- [x] Create `apps/diary-index/__init__.py` and module stubs for `index.py`, `search.py`, `cli.py` with `from __future__ import annotations` and type-hinted signatures.
- [x] Implement the FTS5 schema and `documents` mapping table creation in `index.py`.
- [x] Implement `build_index()` with mtime-based change detection and idempotent inserts/updates/removes.
- [x] Implement `search()` returning ranked `SearchResult` tuples with `snippet()` context.
- [x] Implement `cli.main()` with `index` and `search` subcommands and a `--db` flag.
- [x] Wire "fail loudly": empty folder, missing index, and search-without-index exit 1 with stderr messages.
- [x] Add `tests/test_diary.py` covering index, search and cli runnable via `python3 tests/run_all.py` and `python3 -m pytest -q`.
- [x] Add README snippet documenting the FTS5 schema, idempotent re-indexing, and the read-only source guarantee.
