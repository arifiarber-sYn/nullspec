# diary-index

Local, offline full-text search over a folder of markdown journals. SQLite FTS5 from the Python
standard library, incremental by mtime+size, and it never touches the source files. Built as the
second application on the [`nullspec`](../../README.md) skeleton.

## Run

```bash
python3 apps/diary-index/cli.py index ~/.openclaw/workspace/memory
python3 apps/diary-index/cli.py search "gateway" --limit 3
python3 apps/diary-index/cli.py stats
```

Live run, 2026-11-12: **1 347 markdown files indexed in one pass**, re-run → `unchanged=1347`
(idempotent), query `gateway` returned ranked snippets.

## Contract

- **Schema:** `documents(path PK, mtime, size, title)` + `notes_fts` FTS5 (`path UNINDEXED, title,
  content`, `tokenize='unicode61'`).
- **Idempotent:** unchanged files are skipped by mtime+size; edited files are replaced; deleted
  files are dropped from both tables. Re-indexing the same folder twice adds nothing.
- **Quoted queries:** every token is wrapped in `"` before `MATCH`, so user input cannot inject
  FTS5 syntax.
- **Fail loudly:** missing folder, empty folder, missing index and empty query are all exit 1 with a
  message on stderr.
