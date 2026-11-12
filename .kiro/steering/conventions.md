# Steering — conventions

- Python 3.11+, type hints on public functions, `from __future__ import annotations`.
- One module per concern; the CLI is the only place that prints human text.
- Data classes for records (`@dataclass(frozen=True)`), never bare dicts across module borders.
- Tests live in `tests/`, named `test_<module>.py`, and must pass with `python3 -m pytest -q` **or**
  bare `python3 tests/run_all.py` — the demo machine may not have pytest.
- Every spec task checkbox that flips to `[x]` must be backed by a run in the same commit message.
- Commit style: `spec: ...`, `feat(app): ...`, `fix(skeleton): ...`.
