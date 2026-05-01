from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser


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


def extract_inline_script(html_text: str) -> str:
    parser = _ScriptExtractor()
    parser.feed(html_text)
    return parser.script_text()


def _fetch_json(url: str, timeout: float, payload: dict | None = None) -> tuple[int, dict]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url=url, data=data, headers=headers, method="POST" if payload is not None else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        body = response.read().decode("utf-8")
        return response.status, json.loads(body)


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke check for crane runway local UI server")
    parser.add_argument("--url", default="http://127.0.0.1:8765")
    parser.add_argument("--timeout", type=float, default=10)
    args = parser.parse_args()

    base = args.url.rstrip("/")
    print("LOCAL UI SMOKE CHECK")
    try:
        with urllib.request.urlopen(f"{base}/", timeout=args.timeout) as response:
            html_text = response.read().decode("utf-8")
            if response.status != 200:
                raise ValueError("GET / status")
        print("[1/7] GET / ... PASS")

        status, health = _fetch_json(f"{base}/api/health", args.timeout)
        if status != 200 or health.get("ok") is not True:
            raise ValueError("health")
        print("[2/7] GET /api/health ... PASS")

        status, templates = _fetch_json(f"{base}/api/templates", args.timeout)
        if status != 200 or not isinstance(templates.get("templates"), list):
            raise ValueError("templates")
        print("[3/7] GET /api/templates ... PASS")

        status, case_data = _fetch_json(f"{base}/api/template/ipn-with-cover", args.timeout)
        if status != 200 or not isinstance(case_data, dict):
            raise ValueError("template")
        print("[4/7] GET /api/template/ipn-with-cover ... PASS")

        case_json = json.dumps(case_data)
        status, validation = _fetch_json(f"{base}/api/validate", args.timeout, {"case_json": case_json})
        if status != 200 or "valid" not in validation:
            raise ValueError("validate")
        print("[5/7] POST /api/validate ... PASS")

        status, run_data = _fetch_json(
            f"{base}/api/run",
            args.timeout,
            {"case_json": case_json, "output_formats": ["summary", "html"]},
        )
        if status != 200 or "success" not in run_data:
            raise ValueError("run")
        print("[6/7] POST /api/run ... PASS")

        script_text = extract_inline_script(html_text)
        for fn in ["loadTemplate", "importJsonFile", "validateCase", "runCase", "runUiDiagnostics"]:
            if fn not in script_text:
                raise ValueError(f"missing function {fn}")

        node_bin = shutil.which("node")
        if node_bin:
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tmp:
                tmp.write(script_text)
                script_path = tmp.name
            proc = subprocess.run([node_bin, "--check", script_path], capture_output=True, text=True, check=False)
            if proc.returncode != 0:
                raise ValueError("javascript syntax")
            print("[7/7] JavaScript syntax ... PASS")
        else:
            print("[7/7] JavaScript syntax ... SKIP (node not available)")

    except (urllib.error.URLError, json.JSONDecodeError, ValueError) as exc:
        print(f"RESULT: FAIL ({exc})")
        return 1

    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
