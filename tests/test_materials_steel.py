from __future__ import annotations

import pytest

from section_core.materials import InvalidMaterialError, SteelMaterial, build_sample_steel_materials


def test_steel_material_basic_behavior() -> None:
    material = SteelMaterial(material_id="SAMPLE", Fy_internal_MPa=250.0, Fu_internal_MPa=400.0, E_internal_MPa=200000.0)

    assert material.material_id == "SAMPLE"
    assert material.Fy_MPa() == pytest.approx(250.0)
    assert material.Fu_MPa() == pytest.approx(400.0)
    assert material.E_MPa() == pytest.approx(200000.0)
    assert material.has_Fu() is True
    assert material.metadata == {}

    as_dict = material.to_dict()
    assert as_dict["material_id"] == "SAMPLE"
    assert as_dict["Fy_internal_MPa"] == pytest.approx(250.0)
    assert as_dict["Fu_internal_MPa"] == pytest.approx(400.0)
    assert as_dict["E_internal_MPa"] == pytest.approx(200000.0)
    assert as_dict["metadata"] == {}


def test_steel_material_has_fu_false_when_none() -> None:
    material = SteelMaterial(material_id="NO_FU", Fy_internal_MPa=250.0)
    assert material.has_Fu() is False
    assert material.Fu_MPa() is None


def test_from_values_mpa_and_preserved_fields() -> None:
    material = SteelMaterial.from_values(
        material_id="MPA",
        Fy=300.0,
        Fy_unit="MPa",
        Fu=450.0,
        Fu_unit="MPa",
        E=205000.0,
        E_unit="MPa",
        source="test_source",
        metadata={"grade": "A"},
    )
    assert material.Fy_MPa() == pytest.approx(300.0)
    assert material.Fu_MPa() == pytest.approx(450.0)
    assert material.E_MPa() == pytest.approx(205000.0)
    assert material.source == "test_source"
    assert material.metadata == {"grade": "A"}


def test_from_values_converts_ksi() -> None:
    fy = SteelMaterial.from_values(material_id="FY_KSI", Fy=50.0, Fy_unit="ksi")
    fu = SteelMaterial.from_values(material_id="FU_KSI", Fy=250.0, Fy_unit="MPa", Fu=65.0, Fu_unit="ksi")
    e = SteelMaterial.from_values(material_id="E_KSI", Fy=250.0, Fy_unit="MPa", E=29000.0, E_unit="ksi")

    assert fy.Fy_MPa() == pytest.approx(344.73786465841805)
    assert fu.Fu_MPa() == pytest.approx(448.15922405594345)
    assert e.E_MPa() == pytest.approx(199948.0, rel=1e-4)


def test_density_handling() -> None:
    a = SteelMaterial.from_values(material_id="D0", Fy=250.0, density=7850.0)
    b = SteelMaterial.from_values(material_id="D1", Fy=250.0, density=7850.0, density_unit="kg/m3")
    assert a.density_internal_kg_per_m3 == pytest.approx(7850.0)
    assert b.density_internal_kg_per_m3 == pytest.approx(7850.0)

    with pytest.raises(InvalidMaterialError):
        SteelMaterial.from_values(material_id="D2", Fy=250.0, density=7.85, density_unit="g/cm3")


def test_validation_errors() -> None:
    with pytest.raises(InvalidMaterialError):
        SteelMaterial(material_id="", Fy_internal_MPa=250.0)
    with pytest.raises(InvalidMaterialError):
        SteelMaterial(material_id="X", Fy_internal_MPa=0.0)
    with pytest.raises(InvalidMaterialError):
        SteelMaterial(material_id="X", Fy_internal_MPa=-1.0)
    with pytest.raises(InvalidMaterialError):
        SteelMaterial(material_id="X", Fy_internal_MPa=250.0, Fu_internal_MPa=0.0)
    with pytest.raises(InvalidMaterialError):
        SteelMaterial(material_id="X", Fy_internal_MPa=250.0, E_internal_MPa=-1.0)
    with pytest.raises(InvalidMaterialError):
        SteelMaterial(material_id="X", Fy_internal_MPa=250.0, density_internal_kg_per_m3=-1.0)
    with pytest.raises(InvalidMaterialError):
        SteelMaterial.from_values(material_id="X", Fy=250.0, Fy_unit="badunit")
    with pytest.raises(InvalidMaterialError):
        SteelMaterial.from_values(material_id="X", Fy=250.0, E=200000.0, E_unit="badunit")


def test_sample_materials() -> None:
    materials = build_sample_steel_materials()
    assert isinstance(materials, dict)
    assert "F24" in materials
    assert "F36" in materials
    f24 = materials["F24"]
    f36 = materials["F36"]
    assert f24.Fy_MPa() > 0
    assert f36.Fy_MPa() > f24.Fy_MPa()
    assert f24.metadata["requires_independent_verification_before_design_use"] is True
    assert f36.metadata["not_official_complete_material_library"] is True
