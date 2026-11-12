# service-sentinel

## Requirements

1. The app enumerates systemd user units and docker containers on the local machine using only Python stdlib: `subprocess` to call `systemctl --user` and `http.client` against the docker socket.
   - Acceptance: A unit or container that is unreachable to introspect raises a hard error with a non-zero exit code; it is never silently skipped.

2. Each observed unit/container is classified into exactly one of four states: `ok`, `down`, `restarting`, `unhealthy`.
   - Acceptance: A mapping from raw `systemctl`/docker status strings to the four states is documented in Design and every observed name resolves to exactly one state.

3. The app is read-only by default: it never starts, stops, restarts, or otherwise mutates any unit or container.
   - Acceptance: No code path issues a mutating `systemctl` subcommand or docker API call; a test asserts no mutating verbs appear in the subprocess argument lists.

4. The app emits a single JSON report to stdout describing every observed unit/container, its state, and a timestamp, using frozen dataclasses serialized with `json.dumps`.
   - Acceptance: Output parses as valid JSON, has a top-level `generated_at` and `entries` array, and each entry carries `name`, `kind` (`systemd` | `docker`), and `state`.

5. An empty observation set (no units and no containers found) is an error: the app exits non-zero with a clear message, per the "fail loudly" rule.
   - Acceptance: With both sources returning no entries, the CLI exits 1 and prints a human-readable error to stderr; no empty `{"entries": []}` report is produced.

## Design

Modules (all stdlib, one concern each):

- `collect.py` — gathers raw observations. `collect_systemd_units()` shells out to `systemctl --user list-units --type=service --all --plain` and parses the table; `collect_docker_containers()` talks to `/var/run/docker.sock/containers/json` via `http.client`. Each raw row is returned as a `RawUnit` frozen dataclass (`name`, `kind`, `raw_status`). Unreachable sources raise `CollectorError`.

- `report.py` — maps `RawUnit` rows to a `Status` enum (`OK`, `DOWN`, `RESTARTING`, `UNHEALTHY`) via `classify(raw_status)`, builds a `ReportEntry` frozen dataclass (`name`, `kind`, `state`), and assembles a `Report` frozen dataclass (`generated_at: datetime`, `entries: tuple[ReportEntry, ...]`). `to_json(report) -> str` serializes via `json.dumps` with ISO timestamps.

- `cli.py` — the only module that prints human text. `main()` orchestrates collect -> report -> serialize, writes JSON to stdout, and translates "fail loudly" conditions (`CollectorError`, empty `entries`) into exit code 1 with a stderr message.

Status mapping (raw -> state):

- systemd: `active (running)` / `active (exited)` -> `ok`; `inactive` / `failed` -> `down`; `activating` / `deactivating` -> `restarting`; `failed` with healthcheck semantics -> `unhealthy`.
- docker: `"running"` + healthy -> `ok`; `"exited"` / `"created"` -> `down`; `"restarting"` -> `restarting`; `"running"` + `"unhealthy"` -> `unhealthy`.

Data records (frozen dataclasses, never bare dicts across module borders): `RawUnit`, `ReportEntry`, `Report`, plus `Status(IntEnum)`. Type hints on every public function; `from __future__ import annotations` at the top of each module.

## Tasks

- [x] Create `apps/service-sentinel/__init__.py` and module stubs for `collect.py`, `report.py`, `cli.py` with `from __future__ import annotations` and type-hinted signatures.
- [x] Implement `collect_systemd_units()` in `collect.py` parsing `systemctl --user list-units` output into `RawUnit` rows.
- [x] Implement `collect_docker_containers()` in `collect.py` using `http.client` against the docker socket.
- [x] Define `Status` enum and `classify()` mapping in `report.py` covering all four states for both kinds.
- [x] Implement `Report`, `ReportEntry`, `to_json()` in `report.py` producing valid JSON output.
- [x] Implement `cli.main()` with stdout JSON, stderr error messages, and non-zero exit on failure or empty observation set.
- [x] Add `tests/test_sentinel.py` covering collect, report and cli runnable via `python3 tests/run_all.py` and `python3 -m pytest -q`.
- [x] Add README snippet documenting usage, the four-state model, and the read-only guarantee.
