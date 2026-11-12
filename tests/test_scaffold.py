"""Scaffold tests: a new app gets a valid spec and a runnable entry point."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from nullspec import specs as spec_mod
from nullspec.scaffold import ScaffoldError, new_app

ROOT = Path(__file__).resolve().parents[1]


class ScaffoldTests(unittest.TestCase):
    def test_new_app_creates_valid_spec_and_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = new_app("demo-app", "Demonstrate the skeleton", root=tmp)
            self.assertTrue((target / "app.toml").exists())
            self.assertTrue((target / "main.py").exists())
            found = spec_mod.discover(tmp)
            self.assertEqual([spec.name for spec in found], ["demo-app"])
            self.assertTrue(found[0].ok, found[0].problems)
            self.assertEqual(found[0].total, 4)

    def test_refuses_to_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            new_app("demo-app", "x", root=tmp)
            with self.assertRaises(ScaffoldError):
                new_app("demo-app", "x", root=tmp)

    def test_bad_name_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ScaffoldError):
                new_app("../evil", "x", root=tmp)

    def test_generated_entry_point_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = new_app("demo-app", "Demonstrate the skeleton", root=tmp)
            completed = subprocess.run(
                [sys.executable, str(target / "main.py"), "--self-test"],
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("self-test ok", completed.stdout)


if __name__ == "__main__":
    unittest.main()
