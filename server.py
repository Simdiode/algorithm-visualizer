"""Run: python server.py. No third-party packages required. Python 3.9+."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
from urllib.parse import urlsplit
import webbrowser

from algorithms import SORTS, SEARCHES, visualize
from benchmark import run_benchmarks

WEB = Path(__file__).resolve().parent / "web"
FILES = {"/": ("index.html", "text/html; charset=utf-8"),
         "/index.html": ("index.html", "text/html; charset=utf-8"),
         "/style.css": ("style.css", "text/css; charset=utf-8"),
         "/app.js": ("app.js", "text/javascript; charset=utf-8")}
BENCHMARK_LOCK = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def send_bytes(self, data, content_type, status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; "
                         "script-src 'self'; style-src 'self' 'unsafe-inline'; "
                         "img-src 'self' data:; connect-src 'self'; "
                         "frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(data)

    def json_response(self, value, status=200):
        self.send_bytes(json.dumps(value).encode(), "application/json; charset=utf-8", status)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path in FILES:
            name, mime = FILES[path]
            self.send_bytes((WEB / name).read_bytes(), mime)
        elif path == "/health":
            self.json_response({"ok": True})
        else:
            self.json_response({"error": "Not found."}, 404)

    def do_POST(self):
        # Block cross-origin browser requests; the app never needs external calls.
        origin = self.headers.get("Origin")
        if origin and urlsplit(origin).netloc != self.headers.get("Host"):
            self.json_response({"error": "Cross-origin requests are not allowed."}, 403)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 32768:
                raise ValueError("Request must contain at most 32 KB of JSON.")
            if self.headers.get_content_type() != "application/json":
                raise ValueError("Expected application/json.")
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError("Expected a JSON object.")
            path = urlsplit(self.path).path
            if path == "/api/trace":
                algorithm, values = body.get("algorithm"), body.get("values")
                if not isinstance(algorithm, str) or algorithm not in {**SORTS, **SEARCHES}:
                    raise ValueError("Choose a supported algorithm.")
                if not isinstance(values, list) or not 0 <= len(values) <= 48:
                    raise ValueError("Use at most 48 integers.")
                if any(type(v) is not int or not -999 <= v <= 999 for v in values):
                    raise ValueError("Values must be integers between -999 and 999.")
                target = body.get("target")
                if algorithm in SEARCHES and (type(target) is not int or not -999 <= target <= 999):
                    raise ValueError("Target must be an integer between -999 and 999.")
                self.json_response(visualize(algorithm, values, target))
            elif path == "/api/benchmark":
                group = body.get("group", "sort")
                if group not in ("sort", "search"):
                    raise ValueError("Benchmark group must be sort or search.")
                if not BENCHMARK_LOCK.acquire(blocking=False):
                    self.json_response({"error": "A benchmark is already running. Try again shortly."}, 409)
                    return
                try:
                    self.json_response(run_benchmarks(group))
                finally:
                    BENCHMARK_LOCK.release()
            else:
                self.json_response({"error": "Not found."}, 404)
        except (ValueError, TypeError, UnicodeError) as exc:
            self.json_response({"error": str(exc)}, 400)
        except (BrokenPipeError, ConnectionResetError):
            pass


def main():
    parser = argparse.ArgumentParser(description="Project 21: Algorithm Visualizer")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    parser.add_argument("--no-browser", action="store_true")
    # Development preview runners may pass this; this server always uses a strict port.
    parser.add_argument("--strictPort", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        server = ThreadingHTTPServer((args.host, args.port), Handler)
    except OSError as exc:
        parser.exit(1, f"Could not start server: {exc}\nTry: python server.py --port 8001\n")
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"\nAlgorithm Visualizer: {url}\nPress Ctrl+C to stop.\n", flush=True)
    if not args.no_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
