from pathlib import Path

import pytest

from section_core import Section
from section_core.components import LibraryShapeComponent
from section_core.shapes import load_shape_library_json


def test_cirsoc_sample_library_loads_and_converts_units():
    path = Path(__file__).resolve().parents[1] / "data" / "shape_libraries" / "cirsoc_sample_shapes.json"
    registry = load_shape_library_json(path)

    assert registry.has("CIRSOC_IPN_200")
    assert registry.has("CIRSOC_IPB_200")

    families = registry.list_families()
    assert "IPN" in families
    assert "IPB" in families

    ipn = registry.get("CIRSOC_IPN_200")
    assert ipn.area_mm2 == pytest.approx(3340)
    assert ipn.Iyy_mm4 == pytest.approx(21_400_000)
    assert ipn.Izz_mm4 == pytest.approx(1_170_000)
    assert ipn.Cw_mm6 == pytest.approx(10_520_000_000)

    ipb = registry.get("CIRSOC_IPB_200")
    assert ipb.area_mm2 == pytest.approx(7810)
    assert ipb.Iyy_mm4 == pytest.approx(57_000_000)
    assert ipb.Izz_mm4 == pytest.approx(20_000_000)
    assert ipb.Cw_mm6 == pytest.approx(171_490_000_000)


def test_cirsoc_ipn_component_section_integration_and_metadata():
    path = Path(__file__).resolve().parents[1] / "data" / "shape_libraries" / "cirsoc_sample_shapes.json"
    registry = load_shape_library_json(path)

    component = registry.to_component("CIRSOC_IPN_200", element_id="ipn")
    assert isinstance(component, LibraryShapeComponent)

    section = Section(section_id="cirsoc_ipn_section", components=[component])
    props = section.gross_elastic_properties()
    assert props.area_mm2 == pytest.approx(3340)
    assert props.Iyy_mm4 == pytest.approx(21_400_000)
    assert props.Izz_mm4 == pytest.approx(1_170_000)

    metadata = registry.get("CIRSOC_IPN_200").metadata
    assert metadata is not None
    assert metadata["manually_curated"] is True
    assert metadata["production_complete_library"] is False
    assert metadata["requires_independent_verification_before_design_use"] is True
    assert metadata["axis_mapping"]["table_Ix_maps_to"] == "Iyy_mm4"
    assert metadata["axis_mapping"]["table_Iy_maps_to"] == "Izz_mm4"
