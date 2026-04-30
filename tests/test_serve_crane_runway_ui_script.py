from __future__ import annotations

from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "serve_crane_runway_ui.py"


def test_script_exists() -> None:
    assert SCRIPT.exists()


def test_help_exits_zero_and_has_expected_options() -> None:
    completed = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    assert "--host" in completed.stdout
    assert "--port" in completed.stdout
    assert "--open" in completed.stdout


def test_invalid_argument_exits_two() -> None:
    completed = subprocess.run([sys.executable, str(SCRIPT), "--does-not-exist"], capture_output=True, text=True, check=False)
    assert completed.returncode == 2
