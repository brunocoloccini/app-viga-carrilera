from __future__ import annotations

from pathlib import Path


def test_launcher_wrappers_exist_and_reference_launcher() -> None:
    sh = Path("scripts/start_local_ui_beta.sh")
    ps1 = Path("scripts/start_local_ui_beta.ps1")
    assert sh.exists()
    assert ps1.exists()
    assert "launch_crane_runway_ui.py" in sh.read_text(encoding="utf-8")
    assert "launch_crane_runway_ui.py" in ps1.read_text(encoding="utf-8")


def test_onboarding_doc_content() -> None:
    text = Path("docs/local_ui_beta_onboarding.md").read_text(encoding="utf-8")
    for token in ["First-time setup", "Start the UI", "Create demo project", "Run UI Diagnostics", "Support Bundle", "Known limitations"]:
        assert token in text


def test_distribution_doc_content() -> None:
    text = Path("docs/local_ui_beta_distribution.md").read_text(encoding="utf-8")
    for token in ["handoff", "do not expose UI publicly", "127.0.0.1", "projects/"]:
        assert token in text


def test_release_manifest_content() -> None:
    text = Path("docs/local_ui_beta_release_manifest.md").read_text(encoding="utf-8")
    for token in [
        "launch_crane_runway_ui.py",
        "run_local_ui_rc_check.py",
        "collect_local_ui_support_bundle.py",
        "cirsoc_sample_shapes.json",
        "no official code checks",
    ]:
        assert token in text
