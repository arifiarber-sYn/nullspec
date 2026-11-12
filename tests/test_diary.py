"""diary-index tests: indexing, idempotency, search, loud failures."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import index as diary_index
import search as diary_search


class DiaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "notes"
        self.root.mkdir()
        (self.root / "a.md").write_text("# Dita e parë\n\nGateway u rindez dhe punon.\n", encoding="utf-8")
        (self.root / "b.md").write_text("# Dita e dytë\n\nKujtesa u promovua.\n", encoding="utf-8")
        self.db = Path(self.tmp.name) / "diary.db"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_index_adds_all(self) -> None:
        stats = diary_index.build_index(self.root, self.db)
        self.assertEqual((stats.added, stats.unchanged), (2, 0))
        self.assertEqual(diary_index.document_count(self.db), 2)

    def test_second_run_is_idempotent(self) -> None:
        diary_index.build_index(self.root, self.db)
        stats = diary_index.build_index(self.root, self.db)
        self.assertEqual((stats.added, stats.updated), (0, 0))
        self.assertEqual(stats.unchanged, 2)

    def test_update_and_remove(self) -> None:
        diary_index.build_index(self.root, self.db)
        (self.root / "a.md").write_text("# Ndryshuar\n\nFjalë e re: x402.\n", encoding="utf-8")
        (self.root / "b.md").unlink()
        stats = diary_index.build_index(self.root, self.db)
        self.assertEqual((stats.updated, stats.removed), (1, 1))
        self.assertEqual(diary_index.document_count(self.db), 1)

    def test_search_finds_and_snippets(self) -> None:
        diary_index.build_index(self.root, self.db)
        hits = diary_search.search(self.db, "kujtesa")
        self.assertEqual(len(hits), 1)
        self.assertIn("Kujtesa", hits[0].snippet)

    def test_empty_folder_fails_loudly(self) -> None:
        empty = Path(self.tmp.name) / "empty"
        empty.mkdir()
        with self.assertRaises(diary_index.IndexError_):
            diary_index.build_index(empty, self.db)

    def test_missing_index_fails_loudly(self) -> None:
        with self.assertRaises(diary_index.IndexError_):
            diary_search.search(Path(self.tmp.name) / "nope.db", "gateway")

    def test_fts_query_injection_is_quoted(self) -> None:
        diary_index.build_index(self.root, self.db)
        hits = diary_search.search(self.db, 'gateway" OR "x', limit=5)
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
