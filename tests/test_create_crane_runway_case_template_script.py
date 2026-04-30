from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("scripts/create_crane_runway_case_template.py")


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": "src"},
    )


def test_list_templates() -> None:
    result = _run("--list")
    assert result.returncode == 0
    assert "ipn-with-cover" in result.stdout
    assert "ipn-without-cover" in result.stdout


def test_write_template_success(tmp_path: Path) -> None:
    out = tmp_path / "case.json"
    result = _run("--template", "ipn-with-cover", "--output", str(out))
    assert result.returncode == 0
    assert out.exists()
    assert "WROTE:" in result.stdout
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1.0"


def test_overwrite_flag_required(tmp_path: Path) -> None:
    out = tmp_path / "case.json"
    out.write_text("{}", encoding="utf-8")
    result = _run("--template", "ipn-with-cover", "--output", str(out))
    assert result.returncode == 1

    result2 = _run("--template", "ipn-with-cover", "--output", str(out), "--overwrite")
    assert result2.returncode == 0


def test_unknown_template_exits_1(tmp_path: Path) -> None:
    out = tmp_path / "case.json"
    result = _run("--template", "nope", "--output", str(out))
    assert result.returncode == 1


def test_invalid_arguments_exit_2() -> None:
    result = _run("--template", "ipn-with-cover")
    assert result.returncode == 2
