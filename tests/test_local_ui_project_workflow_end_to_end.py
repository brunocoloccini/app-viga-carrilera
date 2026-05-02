from __future__ import annotations

from io import BytesIO
import json
import zipfile

from section_core.crane_runway.local_web_ui import CraneRunwayLocalWebUi


def test_local_ui_project_workflow_end_to_end(tmp_path) -> None:
    ui = CraneRunwayLocalWebUi(projects_root=tmp_path / "projects")
    project_name = "e2e_project"

    create_resp = ui.handle_request(
        "POST",
        "/api/projects/create",
        body=json.dumps({"project_name": project_name, "template_id": "ipn-with-cover", "overwrite": True}).encode(),
    )
    assert create_resp.status_code == 200

    list_resp = ui.handle_request("GET", "/api/projects")
    projects = json.loads(list_resp.body)
    assert any(item["name"] == project_name for item in projects["projects"])

    case_resp = ui.handle_request("GET", f"/api/projects/{project_name}/case")
    assert case_resp.status_code == 200
    case_payload = json.loads(case_resp.body)
    case_data = case_payload["case_data"]
    case_data.setdefault("metadata", {})["e2e"] = True

    save_resp = ui.handle_request(
        "POST", f"/api/projects/{project_name}/save", body=json.dumps({"case_data": case_data}).encode()
    )
    assert save_resp.status_code == 200

    run_resp = ui.handle_request("POST", f"/api/projects/{project_name}/run")
    run_payload = json.loads(run_resp.body)
    assert run_resp.status_code == 200
    assert run_payload["success"] is True

    hist_resp = ui.handle_request("POST", f"/api/projects/{project_name}/run-history")
    hist_payload = json.loads(hist_resp.body)
    run_id = hist_payload["run_id"]

    runs_resp = ui.handle_request("GET", f"/api/projects/{project_name}/runs")
    runs_payload = json.loads(runs_resp.body)
    assert any(item["run_id"] == run_id for item in runs_payload["runs"])

    summary_resp = ui.handle_request("GET", f"/api/projects/{project_name}/runs/{run_id}/summary")
    assert summary_resp.status_code == 200

    html_resp = ui.handle_request("GET", f"/api/projects/{project_name}/runs/{run_id}/report-html")
    assert html_resp.status_code == 200
    assert json.loads(html_resp.body)["html_report"]

    manifest_resp = ui.handle_request("GET", f"/api/projects/{project_name}/archive-manifest")
    manifest_payload = json.loads(manifest_resp.body)
    assert manifest_payload["project_name"] == project_name

    archive_resp = ui.handle_request("GET", f"/api/projects/{project_name}/archive")
    assert archive_resp.status_code == 200
    with zipfile.ZipFile(BytesIO(archive_resp.body_bytes()), "r") as zf:
        names = zf.namelist()
    assert "input_case.json" in names
    assert "archive_manifest.json" in names

    assert ui.handle_request("POST", "/api/projects/create", body=json.dumps({"project_name": "../bad"}).encode()).status_code == 400
