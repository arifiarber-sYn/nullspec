"""Minimal MCP server over stdio: lets Kiro (or any MCP client) read the plan.

Transport is stdio with newline-delimited JSON-RPC 2.0 — the framing every MCP client
speaks. Two tools only, mirroring the CLI: ``spec_list`` and ``task_next`` (plus
``spec_tasks`` for the whole ledger). No third-party packages: the skeleton stays stdlib.

Run it as ``python3 -m nullspec.mcp --root .`` or ``nullspec mcp --root .``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from . import __version__, specs as spec_mod

PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "nullspec"

TOOLS: list[dict[str, Any]] = [
    {
        "name": "spec_list",
        "description": (
            "List every spec under .kiro/specs with its validity and task progress "
            "(done/total). Use it before choosing what to implement."
        ),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "task_next",
        "description": (
            "Return the next unchecked task of one spec, or null when the spec is complete. "
            "Call this after each edit so the plan and the code never drift."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"spec": {"type": "string", "description": "spec folder name"}},
            "required": ["spec"],
            "additionalProperties": False,
        },
    },
    {
        "name": "spec_tasks",
        "description": "Return every checkbox task of one spec, with its done flag.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "spec": {"type": "string"},
                "include_done": {"type": "boolean", "default": True},
            },
            "required": ["spec"],
            "additionalProperties": False,
        },
    },
]


def _specs(root: Path) -> dict[str, spec_mod.Spec]:
    return {spec.name: spec for spec in spec_mod.discover(root)}


def call_tool(name: str, arguments: dict[str, Any], root: Path) -> Any:
    """Execute one tool call and return its structured result. Raises ValueError on bad input."""
    found = _specs(root)
    if name == "spec_list":
        return {
            "root": str(root),
            "specs": [
                {
                    "name": spec.name,
                    "ok": spec.ok,
                    "done": spec.done,
                    "total": spec.total,
                    "problems": list(spec.problems),
                }
                for spec in found.values()
            ],
        }
    if name in ("task_next", "spec_tasks"):
        wanted = arguments.get("spec")
        if not isinstance(wanted, str) or wanted not in found:
            raise ValueError(
                f"unknown spec {wanted!r}; have: {', '.join(sorted(found)) or 'none'}"
            )
        spec = found[wanted]
        include_done = bool(arguments.get("include_done", True))
        tasks = [task for task in spec.tasks if include_done or not task.done]
        if name == "task_next":
            pending = [task for task in spec.tasks if not task.done]
            return {
                "spec": spec.name,
                "next": pending[0].text if pending else None,
                "remaining": len(pending),
            }
        return {
            "spec": spec.name,
            "tasks": [{"text": task.text, "done": task.done, "line": task.line} for task in tasks],
        }
    raise ValueError(f"unknown tool {name!r}")


def handle(message: dict[str, Any], root: Path) -> dict[str, Any] | None:
    """Handle one JSON-RPC message. Returns the response, or None for notifications."""
    method = message.get("method")
    msg_id = message.get("id")
    if msg_id is None:  # notification (e.g. notifications/initialized) — no response
        return None

    def ok(result: Any) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    def err(code: int, text: str) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": text}}

    if method == "initialize":
        return ok(
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": __version__},
            }
        )
    if method == "ping":
        return ok({})
    if method == "tools/list":
        return ok({"tools": TOOLS})
    if method == "tools/call":
        params = message.get("params") or {}
        name = params.get("name")
        arguments = params.get("arguments") or {}
        try:
            payload = call_tool(name, arguments, root)
        except ValueError as exc:
            return ok(
                {"content": [{"type": "text", "text": f"nullspec: {exc}"}], "isError": True}
            )
        return ok(
            {
                "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
                "isError": False,
            }
        )
    return err(-32601, f"method not found: {method}")


def _messages(stream: Any):
    """Yield JSON-RPC objects, tolerating both newline framing and Content-Length headers."""
    for raw in stream:
        line = raw.strip()
        if not line or line.lower().startswith(b"content-length:"):
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            yield {"jsonrpc": "2.0", "id": None}


def serve(root: Path, stdin: Any = None, stdout: Any = None) -> int:
    stdin = stdin or sys.stdin.buffer
    stdout = stdout or sys.stdout
    for message in _messages(stdin):
        response = handle(message, root)
        if response is None:
            continue
        stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
        stdout.flush()
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="nullspec-mcp", description="MCP stdio server for nullspec")
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    return serve(Path(args.root))


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
