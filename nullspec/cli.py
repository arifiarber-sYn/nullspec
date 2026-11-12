"""CLI: `spec list`, `spec check`, `tasks`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, specs as spec_mod


def _cmd_spec(args: argparse.Namespace) -> int:
    found = spec_mod.discover(args.root)
    if args.action == "list":
        for spec in found:
            state = "ok" if spec.ok else "INVALID"
            print(f"{spec.name:<24} {state:<8} tasks {spec.done}/{spec.total}")
        if not found:
            print("no specs found under .kiro/specs", file=sys.stderr)
            return 1
        return 0
    # check
    bad = [spec for spec in found if not spec.ok]
    for spec in bad:
        print(f"{spec.name}: " + "; ".join(spec.problems), file=sys.stderr)
    if not found:
        print("no specs found", file=sys.stderr)
        return 1
    return 1 if bad else 0


def _cmd_tasks(args: argparse.Namespace) -> int:
    found = {spec.name: spec for spec in spec_mod.discover(args.root)}
    if args.spec not in found:
        print(f"unknown spec {args.spec!r}; have: {', '.join(sorted(found)) or 'none'}", file=sys.stderr)
        return 2
    spec = found[args.spec]
    tasks = [task for task in spec.tasks if args.next is False or not task.done]
    if args.next:
        tasks = tasks[:1]
    if args.json:
        print(json.dumps([{"text": t.text, "done": t.done} for t in tasks], indent=2))
        return 0 if tasks else 1
    for task in tasks:
        print(task)
    return 0 if tasks else 1


def _cmd_new_app(args: argparse.Namespace) -> int:
    from .scaffold import ScaffoldError, new_app

    try:
        target = new_app(args.name, args.purpose, args.root)
    except ScaffoldError as exc:
        print(f"nullspec: {exc}", file=sys.stderr)
        return 1
    print(f"created {target} and .kiro/specs/{args.name}/requirements.md")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nullspec", description="spec-driven skeleton for local apps")
    parser.add_argument("--version", action="version", version=f"nullspec {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    spec = sub.add_parser("spec", help="inspect specs")
    spec.add_argument("action", choices=["list", "check"])
    spec.add_argument("--root", default=".")

    tasks = sub.add_parser("tasks", help="list tasks of a spec")
    tasks.add_argument("--spec", required=True)
    tasks.add_argument("--next", action="store_true", help="print only the next open task")
    tasks.add_argument("--all", dest="next", action="store_false", help="include completed tasks")
    tasks.set_defaults(next=True)
    tasks.add_argument("--json", action="store_true")
    tasks.add_argument("--root", default=".")

    new = sub.add_parser("new-app", help="scaffold a new app from skeleton/template")
    new.add_argument("name")
    new.add_argument("--purpose", required=True)
    new.add_argument("--root", default=".")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "spec":
        return _cmd_spec(args)
    if args.command == "new-app":
        return _cmd_new_app(args)
    return _cmd_tasks(args)
