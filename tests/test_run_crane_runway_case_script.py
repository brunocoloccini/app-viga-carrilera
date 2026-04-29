from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("scripts/run_crane_runway_case.py")


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": "src"},
    )


def test_default_text_output() -> None:
    result = _run("examples/crane_runway_case_demo.json")
    assert result.returncode == 0
    assert "Crane Runway Demand Summary" in result.stdout
    assert not result.stdout.startswith("# ")


def test_markdown_output() -> None:
    result = _run("--markdown", "examples/crane_runway_case_demo.json")
    assert result.returncode == 0
    assert "# Crane Runway Demand Summary" in result.stdout
    assert "## Demands" in result.stdout


def test_both_output() -> None:
    result = _run("--both", "examples/crane_runway_case_demo.json")
    assert result.returncode == 0
    assert "Crane Runway Demand Summary" in result.stdout
    assert "# Crane Runway Demand Summary" in result.stdout
    assert "\n\n---\n\n" in result.stdout


def test_summary_json_output() -> None:
    result = _run("--summary-json", "examples/crane_runway_case_demo.json")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert "summary_id" in payload or "max_vertical_moment_Nmm" in payload


def test_output_file_markdown(tmp_path: Path) -> None:
    out_path = tmp_path / "report.md"
    result = _run("--markdown", "--output", str(out_path), "examples/crane_runway_case_demo.json")
    assert result.returncode == 0
    assert "WROTE:" in result.stdout
    assert out_path.exists()
    assert "# Crane Runway Demand Summary" in out_path.read_text(encoding="utf-8")


def test_invalid_case_missing_schema_version(tmp_path: Path) -> None:
    data = json.loads(Path("examples/crane_runway_case_demo.json").read_text(encoding="utf-8"))
    data.pop("schema_version", None)
    bad = tmp_path / "bad_case.json"
    bad.write_text(json.dumps(data), encoding="utf-8")

    result = _run(str(bad))
    output = result.stdout + result.stderr
    assert result.returncode == 1
    assert "schema_version" in output
    assert "traceback" not in output.lower()


def test_missing_file() -> None:
    result = _run("does/not/exist.json")
    output = result.stdout + result.stderr
    assert result.returncode == 1
    assert "not found" in output.lower()


def test_no_arguments() -> None:
    result = _run()
    assert result.returncode == 2


def test_mutually_exclusive_output_modes() -> None:
    result = _run("--text", "--markdown", "examples/crane_runway_case_demo.json")
    assert result.returncode == 2
