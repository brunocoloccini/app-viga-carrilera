from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "launch_crane_runway_ui.py"
SPEC = importlib.util.spec_from_file_location("launch_crane_runway_ui", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_script_exists() -> None:
    assert SCRIPT.exists()


def test_help_mentions_options() -> None:
    result = _run("--help")
    assert result.returncode == 0
    for token in ["--host", "--port", "--no-open", "--skip-preflight", "--check-only", "--run-smoke-after-start", "--timeout"]:
        assert token in result.stdout


def test_invalid_arg_exits_2() -> None:
    result = _run("--unknown-option")
    assert result.returncode == 2


def test_check_only_passes() -> None:
    result = _run("--check-only", "--no-open")
    out = result.stdout + result.stderr
    assert result.returncode == 0
    for token in ["CRANE RUNWAY LOCAL UI LAUNCHER", "Preflight", "Python import check", "UI module import", "Server port check", "RESULT: PASS"]:
        assert token in out


def test_check_only_fails_when_port_in_use() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        port = sock.getsockname()[1]
        result = _run("--check-only", "--no-open", "--port", str(port))
    out = result.stdout + result.stderr
    assert result.returncode == 1
    assert f"Port {port} appears to be in use." in out
    assert "RESULT: FAIL" in out


def test_port_helper() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        assert MODULE.is_port_available("127.0.0.1", port)
        sock.listen(1)
        assert not MODULE.is_port_available("127.0.0.1", port)


def test_extract_inline_script() -> None:
    html = "<html><script>const x = 1;</script><script src='a.js'></script></html>"
    script = MODULE.extract_inline_script(html)
    assert "const x = 1;" in script
    assert "a.js" not in script


def test_node_syntax_check_reports_skip_or_pass() -> None:
    result = MODULE.run_node_syntax_check("const x = 1;")
    assert result.ok is True
    assert result.detail.startswith("SKIP") or result.detail == "PASS"
