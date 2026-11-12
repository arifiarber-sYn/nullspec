"""Tests for the MCP stdio server: handshake, tool listing and both plan tools."""

from __future__ import annotations

import io
import json
import unittest
from pathlib import Path

from nullspec import mcp

ROOT = Path(__file__).resolve().parents[1]


def rpc(method: str, params: dict | None = None, msg_id: int = 1) -> dict:
    message = {"jsonrpc": "2.0", "id": msg_id, "method": method}
    if params is not None:
        message["params"] = params
    return message


class McpTests(unittest.TestCase):
    def test_initialize_returns_protocol_and_server_info(self):
        response = mcp.handle(rpc("initialize", {"protocolVersion": mcp.PROTOCOL_VERSION}), ROOT)
        assert response is not None
        self.assertEqual(response["result"]["serverInfo"]["name"], "nullspec")
        self.assertEqual(response["result"]["protocolVersion"], mcp.PROTOCOL_VERSION)
        self.assertIn("tools", response["result"]["capabilities"])

    def test_notification_gets_no_response(self):
        self.assertIsNone(mcp.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}, ROOT))

    def test_tools_list_exposes_the_plan_tools(self):
        response = mcp.handle(rpc("tools/list"), ROOT)
        names = [tool["name"] for tool in response["result"]["tools"]]
        self.assertEqual(names, ["spec_list", "task_next", "spec_tasks"])

    def test_spec_list_reports_both_apps_as_valid(self):
        response = mcp.handle(rpc("tools/call", {"name": "spec_list", "arguments": {}}), ROOT)
        payload = json.loads(response["result"]["content"][0]["text"])
        by_name = {spec["name"]: spec for spec in payload["specs"]}
        self.assertEqual(set(by_name), {"diary-index", "service-sentinel"})
        for spec in by_name.values():
            self.assertTrue(spec["ok"], spec["problems"])
            self.assertEqual(spec["done"], spec["total"])

    def test_task_next_on_complete_spec_returns_null(self):
        response = mcp.handle(
            rpc("tools/call", {"name": "task_next", "arguments": {"spec": "diary-index"}}), ROOT
        )
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertIsNone(payload["next"])
        self.assertEqual(payload["remaining"], 0)

    def test_unknown_spec_is_an_error_not_a_crash(self):
        response = mcp.handle(
            rpc("tools/call", {"name": "task_next", "arguments": {"spec": "nope"}}), ROOT
        )
        self.assertTrue(response["result"]["isError"])
        self.assertIn("unknown spec", response["result"]["content"][0]["text"])

    def test_unknown_method_is_jsonrpc_error(self):
        response = mcp.handle(rpc("does/not/exist"), ROOT)
        self.assertEqual(response["error"]["code"], -32601)

    def test_serve_speaks_newline_framed_jsonrpc(self):
        stdin = io.BytesIO(
            b'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n'
            b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n'
            b'{"jsonrpc":"2.0","id":2,"method":"tools/list"}\n'
        )
        stdout = io.StringIO()
        self.assertEqual(mcp.serve(ROOT, stdin=stdin, stdout=stdout), 0)
        replies = [json.loads(line) for line in stdout.getvalue().splitlines()]
        self.assertEqual([reply["id"] for reply in replies], [1, 2])
        self.assertEqual(len(replies[1]["result"]["tools"]), 3)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
