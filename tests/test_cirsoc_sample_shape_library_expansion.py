from pathlib import Path

import pytest

from section_core import Section
from section_core.components import LibraryShapeComponent
from section_core.shapes import load_shape_library_json


def _load_registry():
    path = Path(__file__).resolve().parents[1] / "data" / "shape_libraries" / "cirsoc_sample_shapes.json"
    return load_shape_library_json(path)


def test_cirsoc_sample_library_expansion_loads_and_lists_records():
    registry = _load_registry()

    assert registry.has("CIRSOC_IPN_180")
    assert registry.has("CIRSOC_IPN_200")
    assert registry.has("CIRSOC_IPN_240")
    assert registry.has("CIRSOC_IPN_300")
    assert registry.has("CIRSOC_IPB_200")

    families = registry.list_families()
    assert "IPN" in families
    assert "IPB" in families

    assert len(registry.list_shapes("IPN")) >= 4


def test_cirsoc_sample_library_expansion_unit_conversions():
    registry = _load_registry()

    ipn_180 = registry.get("CIRSOC_IPN_180")
    assert ipn_180.area_mm2 == pytest.approx(2790)
    assert ipn_180.Iyy_mm4 == pytest.approx(14_500_000)
    assert ipn_180.Izz_mm4 == pytest.approx(813_000)
    assert ipn_180.J_mm4 == pytest.approx(78_900)
    assert ipn_180.Cw_mm6 == pytest.approx(5_924_000_000)

    ipn_240 = registry.get("CIRSOC_IPN_240")
    assert ipn_240.area_mm2 == pytest.approx(4610)
    assert ipn_240.Iyy_mm4 == pytest.approx(42_500_000)
    assert ipn_240.Izz_mm4 == pytest.approx(2_210_000)
    assert ipn_240.J_mm4 == pytest.approx(206_000)
    assert ipn_240.Cw_mm6 == pytest.approx(28_730_000_000)

    ipn_300 = registry.get("CIRSOC_IPN_300")
    assert ipn_300.area_mm2 == pytest.approx(6900)
    assert ipn_300.Iyy_mm4 == pytest.approx(98_000_000)
    assert ipn_300.Izz_mm4 == pytest.approx(4_510_000)
    assert ipn_300.J_mm4 == pytest.approx(467_000)
    assert ipn_300.Cw_mm6 == pytest.approx(91_850_000_000)


def test_cirsoc_sample_library_expansion_metadata_and_component_integration():
    registry = _load_registry()

    for shape_id in ("CIRSOC_IPN_180", "CIRSOC_IPN_240", "CIRSOC_IPN_300"):
        metadata = registry.get(shape_id).metadata
        assert metadata is not None
        assert metadata["manually_curated"] is True
        assert metadata["production_complete_library"] is False
        assert metadata["requires_independent_verification_before_design_use"] is True
        assert metadata["axis_mapping"]["table_Ix_maps_to"] == "Iyy_mm4"
        assert metadata["axis_mapping"]["table_Iy_maps_to"] == "Izz_mm4"

    component = registry.to_component("CIRSOC_IPN_300", element_id="ipn_300")
    assert isinstance(component, LibraryShapeComponent)

    section = Section(section_id="cirsoc_ipn_300_section", components=[component])
    props = section.gross_elastic_properties()
    assert props.area_mm2 == pytest.approx(6900)
    assert props.Iyy_mm4 == pytest.approx(98_000_000)
    assert props.Izz_mm4 == pytest.approx(4_510_000)


def test_cirsoc_sample_library_expansion_regression_existing_records_unchanged():
    registry = _load_registry()

    ipn = registry.get("CIRSOC_IPN_200")
    assert ipn.area_mm2 == pytest.approx(3340)
    assert ipn.Iyy_mm4 == pytest.approx(21_400_000)
    assert ipn.Izz_mm4 == pytest.approx(1_170_000)
    assert ipn.J_mm4 == pytest.approx(112_000)
    assert ipn.Cw_mm6 == pytest.approx(10_520_000_000)

    ipb = registry.get("CIRSOC_IPB_200")
    assert ipb.area_mm2 == pytest.approx(7810)
    assert ipb.Iyy_mm4 == pytest.approx(57_000_000)
    assert ipb.Izz_mm4 == pytest.approx(20_000_000)
    assert ipb.J_mm4 == pytest.approx(491_000)
    assert ipb.Cw_mm6 == pytest.approx(171_490_000_000)
