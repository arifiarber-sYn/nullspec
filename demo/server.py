#!/usr/bin/env python3
"""Public, read-only demo of nullspec (Kiroween 2026 judging access).

Serves the real library code from this repository over HTTP so a judge can
exercise the project without installing anything:

    GET  /                 single-page UI
    GET  /api/specs        spec discovery + validation (nullspec.specs)
    GET  /api/tasks?spec=  task ledger for one spec
    POST /api/mcp          JSON-RPC 2.0 request (nullspec.mcp.handle)
    GET  /api/search?q=    FTS5 lookup in a bundled sample corpus

Only reads files inside this repository and a throw-away temp index.
No writes outside the temp directory, no network calls, no credentials.

Usage: python3 demo/server.py --port 8091
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import tempfile
import time
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "apps" / "diary-index"))

from nullspec import mcp as mcp_mod  # noqa: E402
from nullspec import specs as specs_mod  # noqa: E402

import index as diary_index  # noqa: E402  (apps/diary-index)
import search as diary_search  # noqa: E402

RATE_LIMIT = 40  # requests per window per IP
RATE_WINDOW = 60.0
HITS: dict[str, deque[float]] = defaultdict(deque)

DB_PATH = Path(tempfile.mkdtemp(prefix="nullspec-demo-")) / "corpus.db"


def _build_demo_index() -> int:
    stats = diary_index.build_index(ROOT / "demo" / "corpus", DB_PATH)
    return diary_index.document_count(DB_PATH)


DOC_COUNT = 0


def rate_ok(ip: str) -> bool:
    now = time.monotonic()
    q = HITS[ip]
    while q and now - q[0] > RATE_WINDOW:
        q.popleft()
    if len(q) >= RATE_LIMIT:
        return False
    q.append(now)
    return True


def specs_payload() -> dict:
    out = []
    for spec in specs_mod.discover(ROOT):
        out.append(
            {
                "name": spec.name,
                "ok": spec.ok,
                "problems": list(spec.problems),
                "tasks_done": spec.done,
                "tasks_total": spec.total,
                "tasks": [{"done": t.done, "text": t.text} for t in spec.tasks],
            }
        )
    return {"root": ".", "generated_by": "nullspec.specs.discover", "specs": out}


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>nullspec — live demo</title>
<style>
:root{--bg:#0f1115;--fg:#e8e6e3;--dim:#9aa0a6;--acc:#7cc4ff;--ok:#6ee7a8;--card:#181c22}
*{box-sizing:border-box}body{margin:0;font:15px/1.55 ui-sans-serif,system-ui,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--fg)}
main{max-width:900px;margin:0 auto;padding:28px 20px 60px}
h1{font-size:26px;margin:0 0 4px}h2{font-size:17px;margin:26px 0 8px;color:var(--acc)}
p.sub{color:var(--dim);margin:0 0 18px}
.card{background:var(--card);border:1px solid #242a33;border-radius:10px;padding:14px 16px}
pre{margin:8px 0 0;padding:12px;background:#0b0d11;border-radius:8px;overflow:auto;font:12.5px/1.5 ui-monospace,SFMono-Regular,Consolas,monospace;color:#cfd6e4;max-height:340px}
button,input{font:inherit;border-radius:8px;border:1px solid #2f3743;background:#1e2530;color:var(--fg);padding:8px 12px}
button{cursor:pointer}button:hover{border-color:var(--acc)}
input{min-width:220px}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.ok{color:var(--ok)}.dim{color:var(--dim)}
footer{margin-top:28px;color:var(--dim);font-size:13px}
a{color:var(--acc)}
</style></head><body><main>
<h1>nullspec — live demo</h1>
<p class="sub">Read-only HTTP front end over the real repository code (spec validation, task ledger, MCP, FTS5 search). Nothing is installed, nothing is written.</p>

<h2>1 · Spec discovery &amp; validation</h2>
<div class="row"><button onclick="go('specs')">Run nullspec.specs.discover()</button><span class="dim">reads <code>.kiro/specs/*/</code></span></div>
<pre id="specs">—</pre>

<h2>2 · Task ledger</h2>
<div class="row">
  <select id="spec" onchange="tasks()"></select>
  <button onclick="tasks()">Read tasks</button>
</div>
<pre id="tasks">—</pre>

<h2>3 · MCP (JSON-RPC 2.0)</h2>
<div class="row"><button onclick="mcpCall()">POST /api/mcp → tools/call spec_list</button></div>
<pre id="mcp">—</pre>

<h2>4 · Full-text search over a sample journal</h2>
<div class="row"><input id="q" value="hooks" placeholder="term"><button onclick="doSearch()">Search</button></div>
<pre id="search">—</pre>

<footer>Source: <a href="https://github.com/arifiarber-sYn/nullspec">github.com/arifiarber-sYn/nullspec</a> · Python 3.11+ standard library only · demo corpus is synthetic.</footer>

<script>
async function j(url,opt){const r=await fetch(url,opt);const t=await r.text();try{return JSON.stringify(JSON.parse(t),null,2)}catch(e){return t}}
function show(id,v){document.getElementById(id).textContent=v}
async function go(){show('specs','…');const v=await j('api/specs');show('specs',v);try{const d=JSON.parse(v);const s=document.getElementById('spec');if(!s.options.length){d.specs.forEach(x=>{const o=document.createElement('option');o.value=o.textContent=x.name;s.appendChild(o)})}}catch(e){}}
async function tasks(){const s=document.getElementById('spec').value;show('tasks','…');show('tasks',await j('api/tasks?spec='+encodeURIComponent(s)))}
async function mcpCall(){show('mcp','…');show('mcp',await j('api/mcp',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',id:1,method:'tools/call',params:{name:'spec_list',arguments:{}}})}))}
async function doSearch(){const q=document.getElementById('q').value;show('search','…');show('search',await j('api/search?q='+encodeURIComponent(q)))}
go();
</script>
</main></body></html>
"""


class Handler(BaseHTTPRequestHandler):
    server_version = "nullspec-demo/1.0"

    def log_message(self, fmt: str, *args) -> None:  # keep the journal quiet
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload: dict, code: int = 200) -> None:
        self._send(code, json.dumps(payload, indent=2).encode(), "application/json; charset=utf-8")

    def _limited(self) -> bool:
        if not rate_ok(self.client_address[0]):
            self._json({"error": "rate limit: 40 requests/minute"}, 429)
            return True
        return False

    def do_GET(self) -> None:  # noqa: N802
        if self._limited():
            return
        url = urlparse(self.path)
        qs = parse_qs(url.query)
        path = _strip_prefix(url.path)
        if path in ("/", "/index.html"):
            self._send(200, PAGE.encode(), "text/html; charset=utf-8")
            return
        if path == "/api/specs":
            self._json(specs_payload())
            return
        if path == "/api/tasks":
            name = (qs.get("spec") or [""])[0]
            found = {s.name: s for s in specs_mod.discover(ROOT)}
            if name not in found:
                self._json({"error": f"unknown spec {name!r}", "have": sorted(found)}, 404)
                return
            spec = found[name]
            self._json(
                {
                    "spec": spec.name,
                    "done": spec.done,
                    "total": spec.total,
                    "next": next((t.text for t in spec.tasks if not t.done), None),
                    "tasks": [{"done": t.done, "line": t.line, "text": t.text} for t in spec.tasks],
                }
            )
            return
        if path == "/api/search":
            term = (qs.get("q") or [""])[0]
            try:
                rows = diary_search.search(DB_PATH, term, limit=5)
            except Exception as exc:  # IndexError_ and friends
                self._json({"error": str(exc)}, 400)
                return
            self._json(
                {
                    "documents_indexed": DOC_COUNT,
                    "term": term,
                    "results": [
                        {
                            "path": _rel(Path(r.path)),
                            "title": r.title,
                            "snippet": r.snippet,
                        }
                        for r in rows
                    ],
                }
            )
            return
        if path == "/healthz":
            self._json({"ok": True, "documents": DOC_COUNT})
            return
        self._json({"error": "not found"}, 404)

    def do_POST(self) -> None:  # noqa: N802
        if self._limited():
            return
        url = urlparse(self.path)
        if _strip_prefix(url.path) != "/api/mcp":
            self._json({"error": "not found"}, 404)
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length > 8192:
            self._json({"error": "body too large"}, 413)
            return
        try:
            message = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._json({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}, 400)
            return
        reply = mcp_mod.handle(message, ROOT)
        if reply is None:
            self._json({"ok": True, "note": "notification accepted (no response body in MCP)"})
            return
        # Never leak the absolute working directory over a public endpoint.
        self._json(json.loads(json.dumps(reply).replace(str(ROOT), ".")))


def _strip_prefix(path: str) -> str:
    """Tolerate the /nullspec prefix when served behind a path proxy."""
    prefix = "/nullspec"
    if path.startswith(prefix + "/"):
        return path[len(prefix):]
    if path == prefix:
        return "/"
    return path


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return path.name


def main(argv: list[str] | None = None) -> int:
    global DOC_COUNT
    parser = argparse.ArgumentParser(description="nullspec read-only demo server")
    parser.add_argument("--port", type=int, default=8091)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args(argv)
    DOC_COUNT = _build_demo_index()
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"nullspec demo on http://{args.host}:{args.port} (corpus {DOC_COUNT} docs, db {DB_PATH})", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
