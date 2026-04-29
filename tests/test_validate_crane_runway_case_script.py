from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("scripts/validate_crane_runway_case.py")


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": "src"},
    )


def test_script_valid_case() -> None:
    result = _run("examples/crane_runway_case_demo.json")
    assert result.returncode == 0
    assert "VALID" in result.stdout
    assert "examples/crane_runway_case_demo.json" in result.stdout


def test_script_invalid_case_missing_schema_version(tmp_path: Path) -> None:
    bad = tmp_path / "missing_schema_version.json"
    bad.write_text("{}", encoding="utf-8")

    result = _run(str(bad))
    assert result.returncode == 1
    assert "INVALID" in result.stdout
    assert "schema_version" in result.stdout
    assert "Hint:" in result.stdout


def test_script_malformed_json(tmp_path: Path) -> None:
    bad = tmp_path / "malformed.json"
    bad.write_text("{ not json", encoding="utf-8")

    result = _run(str(bad))
    assert result.returncode == 1
    assert "INVALID" in result.stdout
    assert "Invalid JSON" in result.stdout


def test_script_missing_file() -> None:
    result = _run("does/not/exist.json")
    assert result.returncode == 1
    assert "INVALID" in result.stdout


def test_script_no_args() -> None:
    result = _run()
    assert result.returncode == 2
    assert "usage:" in (result.stdout + result.stderr).lower()


def test_script_multiple_files_valid_and_invalid(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{}", encoding="utf-8")

    result = _run("examples/crane_runway_case_demo.json", str(bad))
    assert result.returncode == 1
    assert "VALID: examples/crane_runway_case_demo.json" in result.stdout
    assert f"INVALID: {bad}" in result.stdout
    assert "\n\n" in result.stdout


def test_script_non_strict_allows_missing_schema_version_warning(tmp_path: Path) -> None:
    data = json.loads(Path("examples/crane_runway_case_demo.json").read_text(encoding="utf-8"))
    data.pop("schema_version", None)
    path = tmp_path / "non_strict_case.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    result = _run("--non-strict", str(path))
    assert result.returncode == 0
    assert "VALID" in result.stdout
    assert "INVALID" not in result.stdout
    assert "schema_version" in result.stdout


def test_script_json_output(tmp_path: Path) -> None:
    out = _run("--json", "examples/crane_runway_case_demo.json")
    assert out.returncode == 0
    payload = json.loads(out.stdout)
    assert isinstance(payload, list)
    assert payload[0]["valid"] is True
