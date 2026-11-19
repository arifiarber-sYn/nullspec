# nullspec — Kiroween 2026 submission draft

**Category:** Best Skeleton Crew · **Bonus:** Best Demo (Presentation), Social Blitz
**Repo:** https://github.com/arifiarber-sYn/nullspec (public, MIT detected on 19.11.2026) · **Video:** https://youtu.be/JEoc7i8EPQs — public, 1:53, 1280×720, 25 fps (uploaded 19.11.2026)
**Built:** 11.11.2026 → 12.11.2026 (inside the 30.10–04.12 window) · **Team:** solo

---

## Tagline

A spec-driven skeleton that makes two *different* local apps share one plan — and lets Kiro read
that plan over MCP instead of guessing it.

## What it is

`nullspec` is the shared base of two apps that do unrelated work on one machine:

| App | Job | Real numbers from this machine (12.11.2026) |
|---|---|---|
| `apps/service-sentinel` | Reads systemd user units + Docker containers, reports drift | 234 entries — 103 ok / 131 down / 0 restarting / 0 unhealthy, JSON with `generated_at` |
| `apps/diary-index` | Indexes a markdown journal folder into SQLite FTS5, local search | 1 350 files indexed; re-run → `added=0 updated=0` (idempotent); `search gateway` → ranked hits with snippets |

The skeleton owns exactly four things — everything else belongs to the app:

1. **Spec discovery** — every `.kiro/specs/<name>/` with `## Requirements`, `## Design`, `## Tasks`.
2. **Spec validation** — a half-written spec fails loudly (missing section, no acceptance criterion, no checkbox tasks).
3. **Task ledger** — checkboxes in `tasks.md` are the plan; `tasks --next` returns the next open one.
4. **App registry** — `apps/<name>/app.toml` declares entry point, spec name and health check.

All stdlib, Python 3.11+, zero dependencies — a judge can run it on any machine.

## How Kiro is used (the part that scores)

| Kiro surface | In this repo |
|---|---|
| **Specs first** | `.kiro/specs/diary-index` and `.kiro/specs/service-sentinel` — requirements with acceptance criteria, design (modules + schema), task ledger. Written before the code, 8/8 tasks each, now fully checked. |
| **Steering** | `.kiro/steering/product.md` (stdlib only, read-only by default, files are the database, fail loudly) and `steering/conventions.md` shape every turn. |
| **Hooks** | `.kiro/hooks/test-on-edit.kiro.hook` runs the 28-test suite on edit; `.kiro/hooks/spec-guard.kiro.hook` blocks an edit that would leave a spec invalid. |
| **MCP** | `nullspec/mcp.py` — a stdio JSON-RPC 2.0 server exposing `spec_list`, `task_next`, `spec_tasks`. Kiro can ask "what's next?" instead of re-reading markdown. `python3 -m nullspec mcp --root .` |
| **Scaffold** | `nullspec new-app <name> --purpose "…"` writes a new app folder *and* its spec, so the third app costs one command. |

The `.kiro` folder is committed at the repo root and is **not** in `.gitignore`.

## Why it matters

Local agent tooling rots because the plan lives in a chat and the code lives in a repo. Here the
plan is a file in git, the ledger is machine-readable, and the same skeleton carries two apps
whose requirements share nothing. The pair proves the abstraction: one ledger, two contracts.

## Run it

```bash
python3 -m nullspec spec list                     # both specs, validity + 8/8 tasks
python3 -m nullspec tasks --spec diary-index --next
python3 -m nullspec mcp --root .                  # MCP over stdio
python3 apps/service-sentinel/cli.py --fail-on down   # exit 2 on any down unit
python3 apps/diary-index/cli.py index ~/notes && python3 apps/diary-index/cli.py search gateway
python3 tests/run_all.py                          # 28 tests, OK
```

## Rules checklist (§4 of the official rules)

- [x] New project, built 30.10–04.12.2026 — first commit `3c59d38` 11.11.2026.
- [x] Built with Kiro (CLI 3.1.0, Builder ID login verified 12.11.2026 00:16Z, `ENGINE_OK` turn).
- [x] Working app URL — local CLI; demo video shows the real runs on this machine. No login needed to run.
- [x] Text description of functions — this file.
- [ ] Video demo < 3 min, public YouTube — **recorded 12.11.2026 (112.8 s, verified with ffprobe), upload pending**.
- [ ] Public GitHub repo with MIT visible in About — **repo committed locally, publish pending**.
- [x] `/.kiro` at repo root, not gitignored — tracked files: 2 specs, 2 hooks, 2 steering docs.
- [x] Category + bonus declared — Skeleton Crew + Best Demo + Social Blitz.
- [x] Two distinct apps under one skeleton — `apps/service-sentinel`, `apps/diary-index`.
- [x] Prior art declared: the *idea* of both apps mirrors tooling that already runs on this machine
      (a service watchdog and a memory index); the code in this repo was written inside the window,
      from the specs in `.kiro`, and shares no module with the pre-existing scripts.

## Post copy (Social Blitz)

> #KiroweenHackathon26 one skeleton, two apps, zero dependencies. `nullspec` keeps the plan in
> `.kiro` specs, validates it, and serves it to Kiro over MCP — so the ledger and the code can't
> drift. Built with @kirodotdev for #Kiroween.

**Devpost submission:** id 1311991 (kiroween 2026) — overview + project details + additional info plotësuar 19.11.2026; mbetet pyetja «Kiroween 2025» dhe Submit.
