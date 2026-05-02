from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("scripts/print_local_ui_beta_info.py")


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], env={"PYTHONPATH": "src"}, capture_output=True, text=True)


def test_exists_and_help() -> None:
    assert SCRIPT.exists()
    assert _run("--help").returncode == 0


def test_default_output_contains_required_text() -> None:
    r = _run()
    assert r.returncode == 0
    for token in [
        "LOCAL UI BETA INFO",
        "App Viga Carrilera",
        "Crane Runway Local UI",
        "Internal beta",
        "launch_crane_runway_ui.py",
        "run_beta_health_check.py",
        "no official CIRSOC/CISC/AISC checks",
        "engineering review required",
    ]:
        assert token in r.stdout


def test_json_and_check_files_and_invalid_args() -> None:
    rj = _run("--json")
    assert rj.returncode == 0
    data = json.loads(rj.stdout)
    for key in ["app", "module", "beta_status", "schema_version", "commands", "docs", "limitations"]:
        assert key in data

    rc = _run("--check-files")
    assert rc.returncode == 0

    rb = _run("--nope")
    assert rb.returncode == 2
