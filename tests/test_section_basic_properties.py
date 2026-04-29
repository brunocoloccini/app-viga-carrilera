import pytest

from section_core.components import PlateElement, RectangularElement, SectionElement
from section_core.section.errors import DuplicateComponentError, EmptySectionError, UnsupportedComponentTypeError
from section_core.section.section import Section


class DummyElement(SectionElement):
    def nodes(self):
        return []

    def lines(self):
        return []

    def reference_points(self):
        return {}

    def bounding_box(self):
        return (0.0, 0.0, 0.0, 0.0)

    def transformed(self, transform):
        return self

    def translated(self, dy_mm: float, dz_mm: float):
        return self

    def local_reference(self):
        raise NotImplementedError


def test_single_rectangle_properties():
    rect = RectangularElement.from_center(
        element_id="R1", width=200, width_unit="mm", height=100, height_unit="mm",
        center_y=0, center_y_unit="mm", center_z=0, center_z_unit="mm"
    )
    s = Section(section_id="S1", components=[rect])
    props = s.gross_elastic_properties()

    assert props.area_mm2 == pytest.approx(20000)
    assert props.centroid_y_mm == pytest.approx(0)
    assert props.centroid_z_mm == pytest.approx(0)
    assert props.Iyy_mm4 == pytest.approx(200 * 100**3 / 12)
    assert props.Izz_mm4 == pytest.approx(100 * 200**3 / 12)
    assert props.Iyz_mm4 == pytest.approx(0)
    assert s.bounding_box() == pytest.approx((-100, -50, 100, 50))
    assert props.S_y_top_mm3 == pytest.approx(props.Iyy_mm4 / 50)
    assert props.S_y_bottom_mm3 == pytest.approx(props.Iyy_mm4 / 50)
    assert props.S_z_left_mm3 == pytest.approx(props.Izz_mm4 / 100)
    assert props.S_z_right_mm3 == pytest.approx(props.Izz_mm4 / 100)


def test_two_rectangles_parallel_axis():
    web = RectangularElement.from_center(
        element_id="W", width=20, width_unit="mm", height=200, height_unit="mm",
        center_y=0, center_y_unit="mm", center_z=0, center_z_unit="mm"
    )
    flange = RectangularElement.from_center(
        element_id="F", width=200, width_unit="mm", height=20, height_unit="mm",
        center_y=0, center_y_unit="mm", center_z=110, center_z_unit="mm"
    )
    s = Section(section_id="S2", components=[web, flange])
    props = s.gross_elastic_properties()
    assert props.area_mm2 == pytest.approx(8000)
    zc = (4000 * 0 + 4000 * 110) / 8000
    assert props.centroid_z_mm == pytest.approx(zc)

    web_iyy = 20 * 200**3 / 12 + 4000 * (0 - zc) ** 2
    flg_iyy = 200 * 20**3 / 12 + 4000 * (110 - zc) ** 2
    assert props.Iyy_mm4 == pytest.approx(web_iyy + flg_iyy)

    web_izz = 200 * 20**3 / 12
    flg_izz = 20 * 200**3 / 12
    assert props.Izz_mm4 == pytest.approx(web_izz + flg_izz)


def test_plate_elements_participate_in_properties():
    hp = PlateElement.horizontal_plate(
        element_id="HP", width=100, width_unit="mm", thickness=10, thickness_unit="mm",
        center_y=0, center_y_unit="mm", center_z=50, center_z_unit="mm"
    )
    vp = PlateElement.vertical_plate(
        element_id="VP", thickness=10, thickness_unit="mm", height=100, height_unit="mm",
        center_y=50, center_y_unit="mm", center_z=0, center_z_unit="mm"
    )
    s = Section(section_id="S3", components=[hp, vp])
    props = s.gross_elastic_properties()
    assert props.area_mm2 == pytest.approx(hp.area_mm2() + vp.area_mm2())
    assert props.Iyy_mm4 > 0
    assert props.Izz_mm4 > 0


def test_section_behavior_and_errors():
    s = Section(section_id="S4")
    with pytest.raises(EmptySectionError):
        s.gross_area_mm2()

    r = RectangularElement.from_center(
        element_id="R1", width=20, width_unit="mm", height=10, height_unit="mm",
        center_y=0, center_y_unit="mm", center_z=0, center_z_unit="mm"
    )
    s.add_component(r)
    assert s.component_ids() == ["R1"]
    assert len(s.nodes()) == 4
    assert len(s.lines()) == 4
    assert len(s.reference_points()) >= 5
    assert s.bounding_box() == pytest.approx((-10, -5, 10, 5))

    with pytest.raises(DuplicateComponentError):
        s.add_component(r)

    with pytest.raises(UnsupportedComponentTypeError):
        s.add_component(DummyElement(element_id="D1"))


def test_trace_contains_component_contributions():
    r1 = RectangularElement.from_center(
        element_id="R1", width=10, width_unit="mm", height=10, height_unit="mm",
        center_y=0, center_y_unit="mm", center_z=0, center_z_unit="mm"
    )
    r2 = RectangularElement.from_center(
        element_id="R2", width=20, width_unit="mm", height=10, height_unit="mm",
        center_y=20, center_y_unit="mm", center_z=0, center_z_unit="mm"
    )
    s = Section(section_id="S5", components=[r1, r2])
    props = s.gross_elastic_properties()
    assert props.overlap_check_status == "not_implemented"
    assert len(props.trace) == 2
    assert {item["component_id"] for item in props.trace} == {"R1", "R2"}
    assert all("Iyy_contribution_mm4" in item for item in props.trace)
