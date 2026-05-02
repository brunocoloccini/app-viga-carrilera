from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run local UI release-candidate acceptance checks.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--project-name", default="rc_check_project")
    parser.add_argument("--template", default="ipn-with-cover")
    parser.add_argument("--keep-server", action="store_true")
    parser.add_argument("--skip-archive", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def _build_env() -> dict[str, str]:
    env = os.environ.copy()
    current = env.get("PYTHONPATH", "")
    src = str(SRC_PATH)
    env["PYTHONPATH"] = src if not current else f"{src}{os.pathsep}{current}"
    return env


def http_get_text(url: str) -> tuple[int, str, dict[str, str]]:
    req = urllib.request.Request(url=url, method="GET")
    with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
        return resp.status, resp.read().decode("utf-8"), dict(resp.headers.items())


def http_get_json(url: str) -> tuple[int, dict, dict[str, str]]:
    status, text, headers = http_get_text(url)
    return status, json.loads(text), headers


def http_post_json(url: str, payload: dict) -> tuple[int, dict, dict[str, str]]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url=url, method="POST", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310
        return resp.status, json.loads(resp.read().decode("utf-8")), dict(resp.headers.items())


def wait_for_server(url: str, timeout: float) -> bool:
    start = time.time()
    while time.time() - start <= timeout:
        try:
            status, body, _ = http_get_json(url)
            if status == 200 and body.get("ok") is True:
                return True
        except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, socket.timeout):
            time.sleep(0.2)
    return False


def start_server(host: str, port: int) -> subprocess.Popen[bytes]:
    cmd = [sys.executable, "scripts/serve_crane_runway_ui.py", "--host", host, "--port", str(port)]
    return subprocess.Popen(cmd, cwd=REPO_ROOT, env=_build_env(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def stop_server(proc: subprocess.Popen[bytes] | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def run_check_step(index: int, total: int, name: str, fn):
    try:
        result = fn()
        suffix = f" ({result})" if result else ""
        print(f"[{index}/{total}] {name} ... PASS{suffix}")
        return True
    except Exception as exc:
        print(f"[{index}/{total}] {name} ... FAIL")
        print(f"Reason: {exc}")
        return False


def extract_inline_script(html: str) -> str:
    match = re.search(r"<script>(.*?)</script>", html, flags=re.DOTALL)
    if not match:
        raise ValueError("No inline script found.")
    return match.group(1)


def node_check_script(script_text: str) -> tuple[bool, str]:
    if subprocess.run(["node", "--version"], check=False, capture_output=True).returncode != 0:
        return True, "SKIP (node unavailable)"
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tmp:
        tmp.write(script_text)
        path = tmp.name
    result = subprocess.run(["node", "--check", path], check=False, capture_output=True, text=True)
    Path(path).unlink(missing_ok=True)
    if result.returncode == 0:
        return True, ""
    return False, (result.stderr or result.stdout or "node --check failed").strip()


def is_safe_zip_entry(name: str) -> bool:
    p = Path(name)
    return not p.is_absolute() and ".." not in p.parts


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    base = f"http://{args.host}:{args.port}"
    total = 10
    print("LOCAL UI RC CHECK\n")
    print("Server:")
    print(f"- URL: {base}")
    print(f"- Project: {args.project_name}")
    print(f"- Template: {args.template}\n")

    proc = None
    html = ""
    template_case: dict = {}
    run_id = ""
    ok = True
    proc_ref: dict[str, subprocess.Popen[bytes]] = {}
    try:
        ok &= run_check_step(1, total, "Start server", lambda: _step_start_server(args, base, proc_ref))
        proc = proc_ref.get("proc")
        ok &= run_check_step(2, total, "GET /", lambda: _step_get_root(base))
        status, html, _ = http_get_text(base + "/")
        ok &= run_check_step(3, total, "GET /api/health", lambda: _assert_health(base))
        ok &= run_check_step(4, total, "GET /api/templates", lambda: _step_templates(base, args.template))
        template_case = http_get_json(base + f"/api/template/{args.template}")[1]
        ok &= run_check_step(5, total, "Template validate/run", lambda: _step_validate_run(base, template_case))
        ok &= run_check_step(6, total, "Project create/open/save", lambda: _step_project_cos(base, args.project_name, args.template))
        ok &= run_check_step(7, total, "Project run outputs", lambda: _step_project_run(base, args.project_name))
        run_id_ref: dict[str, str] = {}
        ok &= run_check_step(8, total, "Project run history", lambda: _step_project_history(base, args.project_name, run_id_ref))
        run_id = run_id_ref.get("run_id", "")
        if args.skip_archive:
            print(f"[9/{total}] Project archive export ... SKIP")
        else:
            ok &= run_check_step(9, total, "Project archive export", lambda: _step_archive(base, args.project_name))
        ok &= run_check_step(10, total, "JavaScript syntax", lambda: _step_js(html))
    except KeyboardInterrupt:
        stop_server(proc)
        print("Server stopped.")
        return 1
    finally:
        if not args.keep_server:
            stop_server(proc)

    print(f"\nRESULT: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def _step_start_server(args, base: str, proc_ref: dict) -> None:
    proc = start_server(args.host, args.port)
    proc_ref["proc"] = proc
    if not wait_for_server(base + "/api/health", args.timeout):
        stop_server(proc)
        raise RuntimeError("Server did not become ready within timeout.")


def _step_get_root(base: str) -> None:
    status, text, _ = http_get_text(base + "/")
    assert status == 200
    for token in ["Crane Runway Local UI", "/api/health", "/api/validate", "/api/run", "Project Workspace", "Project Run History", "Project Archive Export"]:
        assert token in text, f"Missing expected page token: {token}"


def _assert_health(base: str) -> None:
    status, payload, _ = http_get_json(base + "/api/health")
    assert status == 200
    assert payload.get("ok") is True


def _step_templates(base: str, template: str) -> None:
    status, payload, _ = http_get_json(base + "/api/templates")
    assert status == 200
    templates = payload.get("templates", [])
    assert any((item == template) or (isinstance(item, dict) and item.get("template_id") == template) for item in templates)
    status, case, _ = http_get_json(base + f"/api/template/{template}")
    assert status == 200
    assert case.get("schema_version") == "1.0"


def _step_validate_run(base: str, case_data: dict) -> None:
    status, payload, _ = http_post_json(base + "/api/validate", {"case_data": case_data})
    assert status == 200 and payload.get("valid") is True
    status, payload, _ = http_post_json(base + "/api/run", {"case_data": case_data, "output_formats": ["summary", "html"]})
    assert status == 200 and payload.get("success") is True
    assert payload.get("summary")
    assert payload.get("html_report")


def _step_project_cos(base: str, project: str, template: str) -> None:
    status, payload, _ = http_post_json(base + "/api/projects/create", {"project_name": project, "template_id": template, "overwrite": True})
    assert status == 200 and payload.get("input_case_path")
    status, payload, _ = http_get_json(base + "/api/projects")
    assert any(item.get("name") == project for item in payload.get("projects", []))
    status, payload, _ = http_get_json(base + f"/api/projects/{project}/case")
    assert payload.get("case_data", {}).get("schema_version") == "1.0"
    case_data = payload["case_data"]
    case_data.setdefault("metadata", {})["rc_check"] = True
    status, payload, _ = http_post_json(base + f"/api/projects/{project}/save", {"case_data": case_data})
    assert status == 200 and payload.get("saved_path")


def _step_project_run(base: str, project: str) -> None:
    status, payload, _ = http_post_json(base + f"/api/projects/{project}/run", {})
    assert status == 200 and payload.get("success") is True
    assert payload.get("summary")


def _step_project_history(base: str, project: str, run_id_ref: dict[str, str]) -> None:
    status, payload, _ = http_post_json(base + f"/api/projects/{project}/run-history", {})
    assert status == 200
    run_id = payload.get("run_id")
    assert run_id
    run_id_ref["run_id"] = run_id
    status, runs_payload, _ = http_get_json(base + f"/api/projects/{project}/runs")
    assert any(run.get("run_id") == run_id for run in runs_payload.get("runs", []))
    status, summary_payload, _ = http_get_json(base + f"/api/projects/{project}/runs/{run_id}/summary")
    assert status == 200 and isinstance(summary_payload, dict)
    status, html_payload, _ = http_get_json(base + f"/api/projects/{project}/runs/{run_id}/report-html")
    assert status == 200 and html_payload.get("html_report")


def _step_archive(base: str, project: str) -> None:
    status, manifest, _ = http_get_json(base + f"/api/projects/{project}/archive-manifest")
    assert status == 200
    assert manifest.get("project_name") == project
    assert isinstance(manifest.get("included_files"), list)
    if "archive_format_version" in manifest:
        assert manifest["archive_format_version"] == "1.0"
    assert manifest.get("notes")
    req = urllib.request.Request(url=base + f"/api/projects/{project}/archive", method="GET")
    with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310
        data = resp.read()
        content_type = resp.headers.get("Content-Type", "")
    assert "application/zip" in content_type or data.startswith(b"PK")
    from io import BytesIO
    with zipfile.ZipFile(BytesIO(data), "r") as zf:
        names = zf.namelist()
    assert "input_case.json" in names and "archive_manifest.json" in names
    for name in names:
        assert is_safe_zip_entry(name), f"Unsafe zip entry: {name}"


def _step_js(html: str) -> str:
    script = extract_inline_script(html)
    for fn_name in ["loadTemplate", "importJsonFile", "validateCase", "runCase", "runUiDiagnostics", "refreshCaseQuality", "refreshProjectList", "runProjectHistorySnapshot", "refreshArchiveManifest"]:
        if f"function {fn_name}" not in script:
            raise AssertionError(f"Missing JS function: {fn_name}")
    ok, detail = node_check_script(script)
    if not ok:
        raise AssertionError(detail)
    return detail


if __name__ == "__main__":
    raise SystemExit(main())
