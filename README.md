# nullspec — spec-driven skeleton for local agent apps

**Kiroween 2026 · Best Skeleton Crew submission**

`nullspec` is a tiny, dependency-free skeleton for building *local* agent applications with a
spec-first workflow. It is the shared base of two distinct apps:

| App | What it does |
|---|---|
| [`apps/service-sentinel`](apps/service-sentinel) | Watches systemd units + Docker containers on the machine and reports drift (down, restarting, unhealthy). |
| [`apps/diary-index`](apps/diary-index) | Indexes a folder of markdown journals into SQLite FTS5 and answers local full-text searches. |

## Why it is a skeleton, not a library

`nullspec` owns exactly four things — everything else belongs to the app:

1. **Spec discovery** — every `.kiro/specs/<name>/` folder with `requirements.md`, `design.md`
   and `tasks.md` is a first-class object.
2. **Spec validation** — required sections (`## Requirements`, `## Design`, `## Tasks`) and at
   least one acceptance criterion per requirement; fails loudly when a spec is half-written.
3. **Task ledger** — reads the `- [ ]` / `- [x]` checkboxes from `tasks.md`, so the plan and the
   code never drift apart.
4. **App registry** — `apps/<name>/app.toml` declares entry point, spec name and health check.

No third-party packages. Python 3.11+ standard library only, so the demo runs anywhere.

## Use

```bash
python3 -m nullspec spec list            # which specs exist and are valid
python3 -m nullspec tasks --spec service-sentinel
python3 -m nullspec tasks --spec service-sentinel --next
python3 -m nullspec mcp --root .         # MCP stdio server: spec_list, task_next, spec_tasks
```

The MCP server speaks newline-framed JSON-RPC 2.0 on stdio, so Kiro (or any MCP client) can read
the plan instead of guessing it:

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"task_next","arguments":{"spec":"service-sentinel"}}}' \
  | python3 -m nullspec.mcp --root .
```

## Kiro usage in this repo

- `.kiro/specs/*` — the specs were written first, in Kiro, before any code.
- `.kiro/steering/` — product + convention steering that shapes every Kiro turn.
- `.kiro/hooks/` — `test-on-edit` and `spec-guard` hooks run the suites automatically.
- `.kiro/powers` / MCP — the skeleton exposes one MCP server (`nullspec.mcp`) with `spec_list`
  and `task_next` tools so Kiro can read the plan directly.

## License

MIT — see [LICENSE](LICENSE).
