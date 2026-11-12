"""service-sentinel — read-only health report for systemd user units and docker containers."""

from __future__ import annotations

import argparse
import sys

from collect import CollectorError, collect_docker_containers, collect_systemd_units
from report import build, to_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="service-sentinel", description=__doc__)
    parser.add_argument("--no-docker", action="store_true", help="skip docker entirely")
    parser.add_argument("--no-systemd", action="store_true", help="skip systemd entirely")
    parser.add_argument("--fail-on", choices=["none", "down", "unhealthy"], default="none",
                        help="exit 2 when an entry reaches this state")
    args = parser.parse_args(argv)

    units = []
    try:
        if not args.no_systemd:
            units.extend(collect_systemd_units())
        if not args.no_docker:
            units.extend(collect_docker_containers())
    except CollectorError as exc:
        print(f"service-sentinel: {exc}", file=sys.stderr)
        return 1

    if not units:
        print("service-sentinel: no units or containers observed — refusing to emit an empty report",
              file=sys.stderr)
        return 1

    report = build(units)
    print(to_json(report))

    states = {entry.state for entry in report.entries}
    if args.fail_on == "down" and "down" in states:
        return 2
    if args.fail_on == "unhealthy" and {"unhealthy", "down"} & states:
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
