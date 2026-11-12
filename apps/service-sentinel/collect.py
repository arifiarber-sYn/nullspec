"""Observation layer — read-only collectors for systemd user units and docker containers."""

from __future__ import annotations

import json
import shutil
import socket
import subprocess
from dataclasses import dataclass

DOCKER_SOCKET = "/var/run/docker.sock"
SYSTEMCTL_ARGS = (
    "systemctl",
    "--user",
    "list-units",
    "--type=service",
    "--all",
    "--plain",
    "--no-legend",
)


class CollectorError(RuntimeError):
    """A source could not be introspected. Never swallowed: the CLI turns it into exit code 1."""


@dataclass(frozen=True)
class RawUnit:
    name: str
    kind: str  # "systemd" | "docker"
    raw_status: str


def collect_systemd_units() -> list[RawUnit]:
    if shutil.which("systemctl") is None:
        raise CollectorError("systemctl not found on this machine")
    try:
        completed = subprocess.run(
            SYSTEMCTL_ARGS, capture_output=True, text=True, timeout=30, check=False
        )
    except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover - platform specific
        raise CollectorError(f"systemctl failed: {exc}") from exc
    if completed.returncode != 0:
        raise CollectorError(f"systemctl exited {completed.returncode}: {completed.stderr.strip()}")
    return parse_systemctl(completed.stdout)


def parse_systemctl(output: str) -> list[RawUnit]:
    units: list[RawUnit] = []
    for line in output.splitlines():
        fields = line.split(None, 4)
        if len(fields) < 4:
            continue
        name, _load, active, sub = fields[0], fields[1], fields[2], fields[3]
        if not name.endswith(".service"):
            continue
        units.append(RawUnit(name=name, kind="systemd", raw_status=f"{active}/{sub}"))
    return units


def collect_docker_containers() -> list[RawUnit]:
    payload = _docker_get("/containers/json?all=1")
    try:
        containers = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise CollectorError(f"docker returned non-JSON: {exc}") from exc
    if not isinstance(containers, list):
        raise CollectorError("docker /containers/json did not return a list")
    units: list[RawUnit] = []
    for item in containers:
        names = item.get("Names") or []
        name = (names[0].lstrip("/") if names else item.get("Id", "")[:12]) or "<unnamed>"
        units.append(RawUnit(name=name, kind="docker", raw_status=str(item.get("State", "unknown"))))
    return units


def _docker_get(path: str) -> str:
    """Minimal HTTP-over-unix-socket GET, stdlib only."""
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect(DOCKER_SOCKET)
    except OSError as exc:
        raise CollectorError(f"docker socket unreachable ({DOCKER_SOCKET}): {exc}") from exc
    with sock:
        request = f"GET {path} HTTP/1.1\r\nHost: docker\r\nConnection: close\r\n\r\n"
        sock.sendall(request.encode("ascii"))
        chunks: list[bytes] = []
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
    head, _, body = b"".join(chunks).partition(b"\r\n\r\n")
    status_line = head.split(b"\r\n", 1)[0].decode("latin-1", "replace")
    if " 200 " not in status_line:
        raise CollectorError(f"docker API returned {status_line!r}")
    if b"transfer-encoding: chunked" in head.lower():
        body = _dechunk(body)
    return body.decode("utf-8", "replace")


def _dechunk(body: bytes) -> bytes:
    out = bytearray()
    while body:
        size_line, _, rest = body.partition(b"\r\n")
        try:
            size = int(size_line.split(b";")[0], 16)
        except ValueError:
            return bytes(out) + body
        if size == 0:
            return bytes(out)
        out += rest[:size]
        body = rest[size + 2 :]
    return bytes(out)
