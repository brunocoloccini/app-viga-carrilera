from __future__ import annotations

import json
from pathlib import Path

from section_core.crane_runway.case_io import run_crane_runway_case_json
from section_core.crane_runway.case_schema import assert_valid_crane_runway_case_dict


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8").lower()


def test_user_case_editing_guide_exists_and_contains_required_topics() -> None:
    path = Path("docs/user_case_editing_guide.md")
    assert path.exists()
    text = _read(str(path))
    for phrase in [
        "projects/mi_viga/input_case.json",
        "span",
        "crane.wheels",
        "cover_plate",
        "material",
        "criteria_presets",
        "rail_eccentricity",
        "no official cirsoc/cisc/aisc checks",
        "no fatigue",
        "no torsional/warping stress",
        "independent verification",
    ]:
        assert phrase in text


def test_editing_examples_exist_validate_and_run() -> None:
    assert Path("examples/editing_guide/README.md").exists()

    for rel_path, expected_cover in [
        ("examples/editing_guide/ipn_with_cover_editing_example.json", True),
        ("examples/editing_guide/ipn_without_cover_editing_example.json", False),
    ]:
        path = Path(rel_path)
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))

        assert data["schema_version"] == "1.0"
        assert data["section"]["cover_plate"]["enabled"] is expected_cover
        assert isinstance(data.get("warnings"), list) and data["warnings"]

        assert_valid_crane_runway_case_dict(data, strict=True)
        result = run_crane_runway_case_json(path)
        assert result.case_id
        assert "max_vertical_moment_Nmm" in result.summary_dict
