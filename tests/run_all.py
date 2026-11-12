#!/usr/bin/env python3
"""Stdlib test runner: `python3 tests/run_all.py` (works with or without pytest installed)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for extra in (ROOT, ROOT / "apps" / "service-sentinel", ROOT / "apps" / "diary-index"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py", top_level_dir=str(ROOT / "tests"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
