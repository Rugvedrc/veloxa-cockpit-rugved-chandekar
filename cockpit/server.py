"""Tiny stdlib HTTP server: the cockpit UI plus a JSON API. Local only (127.0.0.1)."""
import json
import pathlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import agents
from .ask import ask
from .db import connect

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
        con = connect()
        try:
            if self.path == "/":
                return self._send(UI, ctype="text/html")
            if self.path == "/api/worry":
                return self._send([dict(r) for r in con.execute("SELECT * FROM finding ORDER BY severity DESC, id")])
            if self.path == "/api/people":
                return self._send(agents.roster(con))
            if self.path == "/api/claims":
                return self._send([dict(r) for r in con.execute("SELECT * FROM claim ORDER BY id")])
            self._send({"error": "not found"}, 404)
        finally:
            con.close()

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        con = connect()
        try:
            if self.path == "/api/ask":
                return self._send(ask(con, body.get("q", "")))
            if self.path == "/api/interview":
                return self._send(agents.interview(con, body["emp"], body.get("q", "")))
            self._send({"error": "not found"}, 404)
        except KeyError as e:
            self._send({"error": str(e)}, 400)
        finally:
            con.close()

    def log_message(self, *a):
        pass


def serve(port=8765):
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Veloxa cockpit running at http://127.0.0.1:{port}  (Ctrl+C to stop)")
    srv.serve_forever()
