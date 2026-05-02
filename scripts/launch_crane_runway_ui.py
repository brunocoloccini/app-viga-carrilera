from __future__ import annotations

import argparse
from dataclasses import dataclass
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path


class _ScriptExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_script = False
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag.lower() == "script":
            attr_map = {name: value for name, value in attrs}
            if not attr_map.get("src"):
                self._in_script = True

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag.lower() == "script":
            self._in_script = False

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        if self._in_script:
            self._chunks.append(data)

    def script_text(self) -> str:
        return "\n".join(self._chunks)


@dataclass
class CheckResult:
    label: str
    ok: bool
    detail: str = ""


def extract_inline_script(html_text: str) -> str:
    parser = _ScriptExtractor()
    parser.feed(html_text)
    return parser.script_text()


def is_port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock.connect_ex((host, port)) != 0


def run_node_syntax_check(script_text: str) -> CheckResult:
    node_bin = shutil.which("node")
    if not node_bin:
        return CheckResult("Node syntax check", True, "SKIP (node not available)")
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as tmp:
        tmp.write(script_text)
        path = tmp.name
    proc = subprocess.run([node_bin, "--check", path], capture_output=True, text=True, check=False)
    if proc.returncode == 0:
        return CheckResult("Node syntax check", True, "PASS")
    detail = proc.stderr.strip() or "node --check failed"
    return CheckResult("Node syntax check", False, detail)


def run_preflight(host: str, port: int) -> tuple[list[CheckResult], str]:
    checks: list[CheckResult] = []
    html_text = ""

    try:
        import section_core  # noqa: F401
        from section_core.crane_runway.local_web_ui import CraneRunwayLocalWebUi

        checks.append(CheckResult("Python import check", True, "PASS"))
    except Exception as exc:  # pragma: no cover
        checks.append(CheckResult("Python import check", False, str(exc)))
        return checks, html_text

    if is_port_available(host, port):
        checks.append(CheckResult("Server port check", True, "PASS"))
    else:
        checks.append(CheckResult("Server port check", False, f"Port {port} appears to be in use."))

    try:
        ui = CraneRunwayLocalWebUi()
        html_text = ui.render_index_html()
        for token in ["Crane Runway Local UI", "/api/health", "/api/validate", "/api/run"]:
            if token not in html_text:
                raise ValueError(f"missing HTML token: {token}")
        checks.append(CheckResult("UI module import", True, "PASS"))
    except Exception as exc:
        checks.append(CheckResult("UI module import", False, str(exc)))
        return checks, html_text

    checks.append(run_node_syntax_check(extract_inline_script(html_text)))
    return checks, html_text


def smoke_check(base_url: str, timeout: float) -> tuple[bool, str]:
    paths = ["/", "/api/health", "/api/templates"]
    for path in paths:
        try:
            with urllib.request.urlopen(f"{base_url}{path}", timeout=timeout) as response:
                if response.status != 200:
                    return False, f"Smoke check failed: GET {path} returned {response.status}."
        except urllib.error.URLError as exc:
            return False, f"Smoke check failed: GET {path} error: {exc}."
    return True, ""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch crane runway local UI with preflight checks.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    parser.add_argument("--no-open", action="store_true", help="Do not open browser.")
    parser.add_argument("--skip-preflight", action="store_true", help="Skip preflight checks.")
    parser.add_argument("--check-only", action="store_true", help="Run preflight and exit.")
    parser.add_argument("--run-smoke-after-start", action="store_true", help="Run basic smoke checks after server start.")
    parser.add_argument("--timeout", default=10.0, type=float, help="Timeout seconds for smoke checks.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(__file__).resolve().parent.parent
    url = f"http://{args.host}:{args.port}"

    print("CRANE RUNWAY LOCAL UI LAUNCHER\n")
    print(f"Repo root: {repo_root}")
    print(f"URL: {url}\n")

    if not args.skip_preflight:
        print("Preflight:")
        checks, _ = run_preflight(args.host, args.port)
        failed = False
        for check in checks:
            if check.ok and check.detail.startswith("SKIP"):
                print(f"- {check.label}: {check.detail}")
            elif check.ok:
                print(f"- {check.label}: PASS")
            else:
                failed = True
                print(f"- {check.label}: FAIL")
                if check.detail:
                    print(f"  {check.detail}")
        if failed:
            print("\nRESULT: FAIL")
            return 1
        print("\nRESULT: PASS")
    else:
        print("Preflight: SKIPPED")

    if args.check_only:
        return 0

    from section_core.crane_runway.local_web_ui import CraneRunwayLocalWebUi

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

    print("\nStarting server...")
    with ThreadingHTTPServer((args.host, args.port), Handler) as server:
        if not args.no_open:
            webbrowser.open(url)
        print(f"Open in browser: {url}")

        if args.run_smoke_after_start:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            deadline = time.time() + args.timeout
            ok = False
            error = "Timed out waiting for smoke check."
            while time.time() < deadline:
                ok, error = smoke_check(url, args.timeout)
                if ok:
                    break
                time.sleep(0.2)
            if not ok:
                print(error)
                server.shutdown()
                return 1
            print("Smoke check after start: PASS")
            print("Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1.0)
            except KeyboardInterrupt:
                print("Server stopped.")
                server.shutdown()
                return 0

        print("Press Ctrl+C to stop.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("Server stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
