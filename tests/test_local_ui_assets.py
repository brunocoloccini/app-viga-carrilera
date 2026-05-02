from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from section_core.crane_runway.local_ui_assets import (
    render_local_ui_body_html,
    render_local_ui_css,
    render_local_ui_frontend_contract,
    render_local_ui_js,
    render_local_ui_shell_html,
    render_local_ui_version_info,
)


def test_render_local_ui_css_contains_design_system_tokens() -> None:
    css = render_local_ui_css()
    assert css.strip()
    for token in ["--color-bg", ".app-shell", ".app-card", ".tab-button", ".primary-action", ".status-pass", ".empty-state"]:
        assert token in css


def test_render_local_ui_js_contains_constants_and_hooks() -> None:
    js = render_local_ui_js()
    assert js.strip()
    for token in ["LOCAL_UI_BETA_VERSION", "LOCAL_UI_SCHEMA_VERSION", "LOCAL_UI_STORAGE_PREFIX", "initializeLocalUi", "setupActionHandlers", "handleUiAction"]:
        assert token in js


def test_render_local_ui_shell_html_contains_markers() -> None:
    html = render_local_ui_shell_html()
    assert "app-shell" in html
    assert "/assets/local_ui.css" in html
    assert "/assets/local_ui.js" in html
    assert render_local_ui_body_html() in html


def test_render_local_ui_version_info_contains_schema_and_version() -> None:
    info = render_local_ui_version_info()
    assert "1.0" in info
    assert "V1-086" in info


def test_render_local_ui_js_node_check_when_available() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node not available")
    with tempfile.TemporaryDirectory() as tmp_dir:
        js_file = Path(tmp_dir) / "local_ui.js"
        js_file.write_text(render_local_ui_js(), encoding="utf-8")
        subprocess.run([node, "--check", str(js_file)], check=True)


def test_frontend_contract_manifest_basics() -> None:
    c=render_local_ui_frontend_contract(); assert c["contract_version"]=="1.0"; assert c["required_tabs"]; assert c["required_panels"]; assert c["required_actions"]; assert "validateCase" in c["required_functions"]; assert "runCase" in c["required_functions"]; assert "craneRunway.activeTab" in c["required_storage_keys"]; assert "/api/health" in c["required_api_paths"]

def test_js_and_css_cover_contract_tokens() -> None:
    c=render_local_ui_frontend_contract(); js=render_local_ui_js(); css=render_local_ui_css();
    for fn in c["required_functions"]: assert fn in js
    for tok in ["--color-bg",".app-shell",".app-card",".tab-button",".primary-action"]: assert tok in css


def test_v1093_contract_and_js_tokens() -> None:
    c=render_local_ui_frontend_contract(); js=render_local_ui_js()
    for token in ["Beginner Dashboard","Case Wizard","Case Readiness","Wizard Change Summary"]: assert token in c["required_panels"]
    assert "start-case-wizard" in c["required_actions"]
    assert "startCaseWizard" in c["required_functions"]
    assert "craneRunway.caseWizardState" in c["required_storage_keys"]
    for token in ["startCaseWizard","nextWizardStep","validateWizardStep","computeCaseReadiness","updateCaseReadiness"]: assert token in js
