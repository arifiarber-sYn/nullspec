# Steering — product

`nullspec` exists so a local agent app can be **specified once** and then grow without the plan
rotting. The audience is a single developer running tools on their own machine.

Rules that never bend:

- **Stdlib only.** No pip install for the skeleton or the two apps. If a feature needs a
  dependency, it is out of scope.
- **Read-only by default.** Apps in this repo observe the machine; they never mutate it unless a
  spec requirement says so explicitly and the task is checked in `tasks.md`.
- **Files are the database.** Markdown for specs, SQLite (stdlib `sqlite3`) for the diary index,
  JSON for reports.
- **Fail loudly.** A missing spec section, an unreachable unit, or an empty index is an error with
  an exit code — never a silent pass.
