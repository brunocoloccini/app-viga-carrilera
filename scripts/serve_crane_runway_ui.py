from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import webbrowser

from section_core.crane_runway.local_web_ui import CraneRunwayLocalWebUi


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Serve local crane runway web UI.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind.")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind.")
    parser.add_argument("--open", action="store_true", dest="open_browser", help="Open browser after server starts.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    ui = CraneRunwayLocalWebUi()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            self._dispatch()

        def do_POST(self) -> None:  # noqa: N802
            self._dispatch()

        def _dispatch(self) -> None:
            body = None
            length = int(self.headers.get("Content-Length", "0"))
            if length > 0:
                body = self.rfile.read(length)
            response = ui.handle_request(self.command, self.path, body=body)
            self.send_response(response.status_code)
            self.send_header("Content-Type", response.content_type)
            for key, value in response.headers.items():
                self.send_header(key, value)
            payload = response.body_bytes()
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args: object) -> None:
            return

    url = f"http://{args.host}:{args.port}"
    print(f"Serving crane runway UI at {url}")
    if args.open_browser:
        webbrowser.open(url)

    with ThreadingHTTPServer((args.host, args.port), Handler) as server:
        server.serve_forever()


if __name__ == "__main__":
    raise SystemExit(main())
