import pytest

from section_core.geometry import CoordinateFrame, Node, Point2D, UnsupportedCoordinateFrameError
from section_core.units import Dimension, Quantity
from section_core.units.errors import UnitCompatibilityError


def test_point2d_from_values_mm():
    pt = Point2D.from_values(10.0, 25.0, "mm")
    assert pt.y_internal_mm == pytest.approx(10.0)
    assert pt.z_internal_mm == pytest.approx(25.0)


def test_point2d_from_values_inches():
    pt = Point2D.from_values(1.0, 2.0, "in")
    assert pt.y_internal_mm == pytest.approx(25.4)
    assert pt.z_internal_mm == pytest.approx(50.8)


def test_point2d_from_quantities_length():
    pt = Point2D.from_quantities(
        Quantity(100.0, "cm", Dimension.LENGTH),
        Quantity(1.0, "m", Dimension.LENGTH),
    )
    assert pt.y_internal_mm == pytest.approx(1000.0)
    assert pt.z_internal_mm == pytest.approx(1000.0)


def test_point2d_rejects_non_length_quantities():
    with pytest.raises(UnitCompatibilityError):
        Point2D.from_quantities(Quantity(10, "kN", Dimension.FORCE), Quantity(1, "m", Dimension.LENGTH))


def test_node_defaults():
    node = Node(node_id="N1", name="Node 1", y_internal_mm=1.5, z_internal_mm=2.5)
    assert node.node_type == "vertex"
    assert node.element_id is None


def test_fixed_origin_roundtrip():
    frame = CoordinateFrame.fixed(100.0, 50.0)
    local = frame.internal_to_local(130.0, 70.0)
    assert local == pytest.approx((30.0, 20.0))
    internal = frame.local_to_internal(30.0, 20.0)
    assert internal == pytest.approx((130.0, 70.0))


def test_local_to_internal_with_units():
    frame = CoordinateFrame.fixed(0.0, 0.0)
    y_i, z_i = frame.local_to_internal(1.0, 2.0, units="in")
    assert y_i == pytest.approx(25.4)
    assert z_i == pytest.approx(50.8)


def test_node_linked_origin_tracks_node_replacement():
    node = Node(node_id="N1", name="A", y_internal_mm=10.0, z_internal_mm=20.0)
    frame = CoordinateFrame.from_node(node, frozen=False)
    assert frame.origin_internal() == pytest.approx((10.0, 20.0))


def test_node_frozen_origin_keeps_initial_position():
    node = Node(node_id="N2", name="B", y_internal_mm=11.0, z_internal_mm=22.0)
    frame = CoordinateFrame.from_node(node, frozen=True)
    assert frame.origin_internal() == pytest.approx((11.0, 22.0))


def test_centroid_dynamic_origin_updates():
    centroid = {"v": (5.0, 6.0)}

    def centroid_fn():
        return centroid["v"]

    frame = CoordinateFrame.from_centroid(centroid_fn, frozen=False)
    assert frame.origin_internal() == pytest.approx((5.0, 6.0))
    centroid["v"] = (7.0, 8.0)
    assert frame.origin_internal() == pytest.approx((7.0, 8.0))


def test_centroid_frozen_origin_remains_constant():
    centroid = {"v": (2.0, 3.0)}

    def centroid_fn():
        return centroid["v"]

    frame = CoordinateFrame.from_centroid(centroid_fn, frozen=True)
    centroid["v"] = (9.0, 11.0)
    assert frame.origin_internal() == pytest.approx((2.0, 3.0))


def test_rotation_not_supported():
    with pytest.raises(UnsupportedCoordinateFrameError):
        CoordinateFrame(rotation_deg=15.0)
