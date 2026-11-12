"""service-sentinel tests: parsing, classification, read-only guarantee."""

from __future__ import annotations

import inspect
import unittest

import collect
import report

SYSTEMCTL_SAMPLE = """\
avokatim-db.service loaded active running AvokatIM db
bad.service loaded failed failed Something broke
oneshot.service loaded active exited Finished job
"""

DOCKER_SAMPLE = """[
  {"Names": ["/avokatim-db"], "State": "running"},
  {"Names": ["/tmp-worker"], "State": "exited"},
  {"Id": "0123456789abcdef", "State": "weird-state"}
]"""


class SentinelTests(unittest.TestCase):
    def test_parse_systemctl(self) -> None:
        units = collect.parse_systemctl(SYSTEMCTL_SAMPLE)
        self.assertEqual([u.name for u in units], ["avokatim-db.service", "bad.service", "oneshot.service"])
        self.assertEqual(units[0].raw_status, "active/running")

    def test_classify_every_state(self) -> None:
        self.assertIs(report.classify("active/running"), report.Status.OK)
        self.assertIs(report.classify("failed/failed"), report.Status.DOWN)
        self.assertIs(report.classify("activating/auto-restart"), report.Status.RESTARTING)
        self.assertIs(report.classify("paused"), report.Status.UNHEALTHY)
        self.assertIs(report.classify("nonsense"), report.Status.UNHEALTHY)

    def test_build_is_sorted_and_counted(self) -> None:
        units = [
            collect.RawUnit("b", "docker", "running"),
            collect.RawUnit("a", "systemd", "failed/failed"),
        ]
        built = report.build(units)
        self.assertEqual([e.name for e in built.entries], ["b", "a"])  # docker before systemd
        self.assertEqual(built.counts["ok"], 1)
        self.assertEqual(built.counts["down"], 1)
        self.assertIn('"generated_at"', report.to_json(built))

    def test_no_mutating_verbs_in_collector(self) -> None:
        source = inspect.getsource(collect)
        forbidden = (" start ", " stop ", " restart ", " enable ", " disable ", " rm ", " kill ")
        self.assertEqual(collect.SYSTEMCTL_ARGS[1], "--user")
        for verb in forbidden:
            self.assertNotIn(verb, source, f"collector must stay read-only, found {verb!r}")
        self.assertIn("/containers/json", source)


if __name__ == "__main__":
    unittest.main()
