from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPT = Path("scripts/init_crane_runway_project.py")
VALIDATE_SCRIPT = Path("scripts/validate_crane_runway_case.py")


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": "src"},
    )


def _run_validate(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": "src"},
    )


def test_basic_create(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    result = _run("--name", "test_project", "--template", "ipn-with-cover", "--root", str(root))
    assert result.returncode == 0
    assert (root / "test_project" / "input_case.json").exists()
    assert (root / "test_project" / "README.md").exists()
    assert (root / "test_project" / "outputs").is_dir()
    assert "CREATED:" in result.stdout


def test_generated_case_validates(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    _run("--name", "test_project", "--template", "ipn-with-cover", "--root", str(root))
    result = _run_validate(str(root / "test_project" / "input_case.json"))
    assert result.returncode == 0


def test_validate_flag(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    result = _run("--name", "test_project", "--template", "ipn-with-cover", "--root", str(root), "--validate")
    assert result.returncode == 0
    assert "VALID:" in result.stdout


def test_run_flag(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    result = _run("--name", "test_project", "--template", "ipn-with-cover", "--root", str(root), "--run")
    assert result.returncode == 0
    assert (root / "test_project" / "outputs" / "manifest.json").exists()
    assert (root / "test_project" / "outputs" / "report.html").exists()
    assert "PACKAGE WROTE:" in result.stdout


def test_existing_non_empty_without_overwrite(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    first = _run("--name", "test_project", "--template", "ipn-with-cover", "--root", str(root))
    assert first.returncode == 0
    second = _run("--name", "test_project", "--template", "ipn-with-cover", "--root", str(root))
    assert second.returncode == 1


def test_existing_with_overwrite(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    first = _run("--name", "test_project", "--template", "ipn-with-cover", "--root", str(root))
    assert first.returncode == 0
    second = _run("--name", "test_project", "--template", "ipn-with-cover", "--root", str(root), "--overwrite")
    assert second.returncode == 0


def test_invalid_project_names(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    for bad_name in ("../bad", "bad/name", "bad name"):
        result = _run("--name", bad_name, "--template", "ipn-with-cover", "--root", str(root))
        assert result.returncode == 1

    empty_result = _run("--name", "", "--template", "ipn-with-cover", "--root", str(root))
    assert empty_result.returncode == 1


def test_unknown_template_exits_1(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    result = _run("--name", "test_project", "--template", "unknown-template", "--root", str(root))
    assert result.returncode == 1


def test_missing_args_exit_2() -> None:
    result = _run("--name", "only_name")
    assert result.returncode == 2
