import pytest

from section_core.geometry import (
    DegenerateGeometryError,
    GeometryMergeError,
    GeometryTolerance,
    InvalidToleranceError,
    Node,
    SectionLine,
    SectionPoint,
)


def test_default_tolerance_creation():
    tol = GeometryTolerance.default()
    assert tol.point_merge_abs_tol_mm == pytest.approx(1e-6)
    assert tol.min_segment_length_mm == pytest.approx(1e-9)


def test_invalid_tolerance_values_rejected():
    with pytest.raises(InvalidToleranceError):
        GeometryTolerance(
            point_merge_abs_tol_mm=0.0,
            line_merge_abs_tol_mm=1e-6,
            parallel_abs_tol=1e-12,
            collinear_abs_tol_mm=1e-6,
            min_segment_length_mm=1e-9,
        )


def test_section_point_creation_mm():
    p = SectionPoint.from_values("P1", 10, 20, unit="mm")
    assert p.as_tuple() == pytest.approx((10.0, 20.0))


def test_section_point_creation_inches():
    p = SectionPoint.from_values("P1", 1, 2, unit="in")
    assert p.as_tuple() == pytest.approx((25.4, 50.8))


def test_section_point_from_node():
    n = Node(node_id="N1", name="N", y_internal_mm=3.0, z_internal_mm=4.0)
    p = SectionPoint.from_node(n)
    assert p.point_id == "N1"
    assert p.as_tuple() == pytest.approx((3.0, 4.0))


def test_distance_to():
    p1 = SectionPoint.from_values("P1", 0, 0)
    p2 = SectionPoint.from_values("P2", 3, 4)
    assert p1.distance_to(p2) == pytest.approx(5.0)


def test_is_close_to():
    tol = GeometryTolerance.default()
    p1 = SectionPoint.from_values("P1", 0, 0)
    p2 = SectionPoint.from_values("P2", 5e-7, 0)
    assert p1.is_close_to(p2, tol)


def test_section_line_length():
    l = SectionLine("L1", SectionPoint.from_values("A", 0, 0), SectionPoint.from_values("B", 3, 4))
    assert l.length_mm == pytest.approx(5.0)


def test_section_line_rejects_coincident_points():
    with pytest.raises(DegenerateGeometryError):
        SectionLine("L1", SectionPoint.from_values("A", 0, 0), SectionPoint.from_values("B", 0, 0))


def test_section_line_direction_vector():
    l = SectionLine("L1", SectionPoint.from_values("A", 0, 0), SectionPoint.from_values("B", 3, 4))
    assert l.direction == pytest.approx((0.6, 0.8))


def test_section_line_midpoint():
    l = SectionLine("L1", SectionPoint.from_values("A", 0, 0), SectionPoint.from_values("B", 2, 2))
    assert l.midpoint.as_tuple() == pytest.approx((1.0, 1.0))


def test_contains_point_on_segment():
    tol = GeometryTolerance.default()
    l = SectionLine("L1", SectionPoint.from_values("A", 0, 0), SectionPoint.from_values("B", 10, 0))
    assert l.contains_point(SectionPoint.from_values("P", 5, 0), tol)


def test_contains_point_outside_segment():
    tol = GeometryTolerance.default()
    l = SectionLine("L1", SectionPoint.from_values("A", 0, 0), SectionPoint.from_values("B", 10, 0))
    assert not l.contains_point(SectionPoint.from_values("P", 11, 0), tol)


def test_parallel_lines_detection():
    tol = GeometryTolerance.default()
    l1 = SectionLine("L1", SectionPoint.from_values("A", 0, 0), SectionPoint.from_values("B", 10, 0))
    l2 = SectionLine("L2", SectionPoint.from_values("C", 0, 5), SectionPoint.from_values("D", 10, 5))
    assert l1.is_parallel_to(l2, tol)


def test_collinear_lines_detection():
    tol = GeometryTolerance.default()
    l1 = SectionLine("L1", SectionPoint.from_values("A", 0, 0), SectionPoint.from_values("B", 10, 0))
    l2 = SectionLine("L2", SectionPoint.from_values("C", 10, 0), SectionPoint.from_values("D", 20, 0))
    assert l1.is_collinear_with(l2, tol)


def test_merge_touching_collinear_segments():
    tol = GeometryTolerance.default()
    l1 = SectionLine("L1", SectionPoint.from_values("A", 0, 0), SectionPoint.from_values("B", 10, 0))
    l2 = SectionLine("L2", SectionPoint.from_values("C", 10, 0), SectionPoint.from_values("D", 20, 0))
    merged = l1.merged_with(l2, tol)
    assert merged.start.as_tuple() == pytest.approx((0.0, 0.0))
    assert merged.end.as_tuple() == pytest.approx((20.0, 0.0))


def test_merge_overlapping_collinear_segments():
    tol = GeometryTolerance.default()
    l1 = SectionLine("L1", SectionPoint.from_values("A", 0, 0), SectionPoint.from_values("B", 10, 0))
    l2 = SectionLine("L2", SectionPoint.from_values("C", 5, 0), SectionPoint.from_values("D", 20, 0))
    merged = l1.merged_with(l2, tol)
    assert merged.start.as_tuple() == pytest.approx((0.0, 0.0))
    assert merged.end.as_tuple() == pytest.approx((20.0, 0.0))


def test_reject_merge_parallel_non_collinear_segments():
    tol = GeometryTolerance.default()
    l1 = SectionLine("L1", SectionPoint.from_values("A", 0, 0), SectionPoint.from_values("B", 10, 0))
    l2 = SectionLine("L2", SectionPoint.from_values("C", 0, 2), SectionPoint.from_values("D", 10, 2))
    with pytest.raises(GeometryMergeError):
        l1.merged_with(l2, tol)


def test_reject_merge_non_parallel_segments():
    tol = GeometryTolerance.default()
    l1 = SectionLine("L1", SectionPoint.from_values("A", 0, 0), SectionPoint.from_values("B", 10, 0))
    l2 = SectionLine("L2", SectionPoint.from_values("C", 0, 0), SectionPoint.from_values("D", 0, 10))
    with pytest.raises(GeometryMergeError):
        l1.merged_with(l2, tol)
