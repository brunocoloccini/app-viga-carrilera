from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("scripts/run_beta_health_check.py")


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": "src"},
    )


def _load_script_module():
    spec = importlib.util.spec_from_file_location("run_beta_health_check", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_script_exists() -> None:
    assert SCRIPT.exists()


def test_skip_pytest_succeeds() -> None:
    result = _run("--skip-pytest")
    assert result.returncode == 0
    assert "BETA HEALTH CHECK" in result.stdout
    assert "Public API import check" in result.stdout
    assert "__all__ binding audit" in result.stdout
    assert "CLI smoke checks" in result.stdout
    assert "RESULT: PASS" in result.stdout


def test_quiet_mode_shorter_output() -> None:
    normal = _run("--skip-pytest")
    quiet = _run("--skip-pytest", "--quiet")
    assert quiet.returncode == 0
    assert "RESULT: PASS" in quiet.stdout
    assert len(quiet.stdout) < len(normal.stdout)


def test_invalid_argument() -> None:
    result = _run("--unknown")
    assert result.returncode == 2


def test_all_binding_audit_no_missing_exports() -> None:
    module = _load_script_module()
    assert module.audit_all_bindings() == []
