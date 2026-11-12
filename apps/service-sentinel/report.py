"""Classification and JSON report assembly."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum

from collect import RawUnit


class Status(str, Enum):
    OK = "ok"
    DOWN = "down"
    RESTARTING = "restarting"
    UNHEALTHY = "unhealthy"


SYSTEMD_MAP = {
    "active/running": Status.OK,
    "active/exited": Status.OK,  # oneshot units that finished successfully
    "activating/start": Status.RESTARTING,
    "activating/auto-restart": Status.RESTARTING,
    "reloading/reload": Status.RESTARTING,
    "deactivating/stop": Status.DOWN,
    "failed/failed": Status.DOWN,
    "inactive/dead": Status.DOWN,
}

DOCKER_MAP = {
    "running": Status.OK,
    "restarting": Status.RESTARTING,
    "created": Status.RESTARTING,
    "paused": Status.UNHEALTHY,
    "exited": Status.DOWN,
    "dead": Status.DOWN,
}


def classify(raw_status: str) -> Status:
    """Map a raw status to exactly one state; unknown values are unhealthy, never ignored."""
    return SYSTEMD_MAP.get(raw_status) or DOCKER_MAP.get(raw_status) or Status.UNHEALTHY


@dataclass(frozen=True)
class ReportEntry:
    name: str
    kind: str
    state: str


@dataclass(frozen=True)
class Report:
    generated_at: datetime
    entries: tuple[ReportEntry, ...]

    @property
    def counts(self) -> dict[str, int]:
        tally = {status.value: 0 for status in Status}
        for entry in self.entries:
            tally[entry.state] = tally.get(entry.state, 0) + 1
        return tally


def build(units: list[RawUnit], now: datetime | None = None) -> Report:
    entries = tuple(
        ReportEntry(name=unit.name, kind=unit.kind, state=classify(unit.raw_status).value)
        for unit in sorted(units, key=lambda u: (u.kind, u.name))
    )
    return Report(generated_at=now or datetime.now(timezone.utc), entries=entries)


def to_json(report: Report) -> str:
    payload = {
        "generated_at": report.generated_at.replace(microsecond=0).isoformat(),
        "counts": report.counts,
        "entries": [asdict(entry) for entry in report.entries],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
