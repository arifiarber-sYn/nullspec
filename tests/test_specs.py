"""Skeleton tests: spec discovery, validation, task parsing."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nullspec import specs as spec_mod

GOOD = """# demo

## Requirements

1. Something.
   - Acceptance: it works.

## Design

This design explains the modules, the data flow, the records and the failure modes clearly enough
that a second developer could rebuild the app from this section alone without asking questions.

## Tasks

- [x] first task
- [ ] second task
"""


class SpecTests(unittest.TestCase):
    def test_valid_spec_has_no_problems(self) -> None:
        self.assertEqual(spec_mod.validate(GOOD), [])

    def test_missing_section_is_reported(self) -> None:
        broken = GOOD.replace("## Design", "## Other")
        problems = spec_mod.validate(broken)
        self.assertTrue(any("## Design" in problem for problem in problems))

    def test_missing_acceptance_is_reported(self) -> None:
        problems = spec_mod.validate(GOOD.replace("Acceptance:", "Note:"))
        self.assertTrue(any("acceptance" in problem for problem in problems))

    def test_tasks_parse_marks(self) -> None:
        tasks = spec_mod.parse_tasks(GOOD)
        self.assertEqual([t.text for t in tasks], ["first task", "second task"])
        self.assertTrue(tasks[0].done)
        self.assertFalse(tasks[1].done)

    def test_discover_reads_folder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / ".kiro" / "specs" / "demo"
            folder.mkdir(parents=True)
            (folder / "requirements.md").write_text(GOOD, encoding="utf-8")
            found = spec_mod.discover(tmp)
            self.assertEqual(len(found), 1)
            self.assertTrue(found[0].ok)
            self.assertEqual((found[0].done, found[0].total), (1, 2))


if __name__ == "__main__":
    unittest.main()
