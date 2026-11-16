"""Tiny stdlib HTTP server: the cockpit UI plus a JSON API. Local only (127.0.0.1).

Every endpoint takes an optional `as_of` (YYYY-MM-DD): the answer then uses only material
released on or before that date.
"""
import json
import pathlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import agents
from . import build as builder

UI = (pathlib.Path(__file__).parent / "ui.html").read_bytes()


class Handler(BaseHTTPRequestHandler):
    def _send(self, obj, status=200, ctype="application/json"):
        data = obj if isinstance(obj, bytes) else json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        as_of = (parse_qs(url.query).get("as_of") or [None])[0] or None
        try:
            if url.path == "/":
                return self._send(UI, ctype="text/html")
            if url.path == "/api/worry":
                return self._send(builder.table("SELECT * FROM finding ORDER BY severity DESC, id", as_of))
            if url.path == "/api/claims":
                return self._send(builder.table("SELECT * FROM claim ORDER BY id", as_of))
            if url.path == "/api/people":
                con = builder.get_con(as_of)
                try:
                    return self._send(agents.roster(con))
                finally:
                    con.close()
            self._send({"error": "not found"}, 404)
        except builder.NothingReleased:
            self._send([])  # nothing released yet: empty views

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        as_of = body.get("as_of") or None
        try:
            if self.path == "/api/ask":
                return self._send(builder.answer(body.get("q", ""), as_of))
            if self.path == "/api/interview":
                con = builder.get_con(as_of)
                try:
                    return self._send(agents.interview(con, body["emp"], body.get("q", "")))
                finally:
                    con.close()
            self._send({"error": "not found"}, 404)
        except (KeyError, builder.NothingReleased) as e:
            self._send({"error": f"{type(e).__name__}: {e}"}, 400)

    def log_message(self, *a):
        pass


def serve(port=8765):
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Veloxa cockpit running at http://127.0.0.1:{port}  (Ctrl+C to stop)")
    srv.serve_forever()
