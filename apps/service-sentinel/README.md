# service-sentinel

Read-only health snapshot of every systemd **user** unit and every Docker container on the machine,
as one JSON report. Built as the first application on the [`nullspec`](../../README.md) skeleton.

## Run

```bash
python3 apps/service-sentinel/cli.py                 # full report (systemd + docker)
python3 apps/service-sentinel/cli.py --no-docker     # systemd only
python3 apps/service-sentinel/cli.py --fail-on down  # exit 2 if anything is down (cron/monitor)
```

Live run on this machine, 2026-11-12T00:17:59Z: **234 entries — 102 ok, 132 down, 0 restarting, 0 unhealthy**.

## Contract

- **Read-only.** The collector only ever runs `systemctl --user list-units` and
  `GET /var/run/docker.sock/containers/json`. `tests/test_sentinel.py` asserts no mutating verb is
  present in the source.
- **Fail loudly.** An unreachable source raises `CollectorError` → exit 1; an empty observation set
  is an error, not an empty report.
- **Four states only:** `ok`, `down`, `restarting`, `unhealthy` (unknown raw values map to
  `unhealthy`, never to a silent pass).

## Output

```json
{
  "generated_at": "2026-11-12T00:17:59+00:00",
  "counts": {"ok": 102, "down": 132, "restarting": 0, "unhealthy": 0},
  "entries": [{"name": "avokatim-db", "kind": "docker", "state": "ok"}]
}
```
