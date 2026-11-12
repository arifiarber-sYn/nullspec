# {name}

## Requirements

1. {purpose}
   - Acceptance: describe the observable result, not the implementation.

## Design

Explain the modules, the data flow, the records and every failure mode. A second developer should be
able to rebuild the app from this section without asking questions. Keep it stdlib only and
read-only unless a requirement below says otherwise.

## Tasks

- [ ] Write the collector/input module for {name}.
- [ ] Write the transform/report module for {name}.
- [ ] Write the CLI with exit codes for every failure mode.
- [ ] Add tests under `tests/` and run them with `python3 tests/run_all.py`.
