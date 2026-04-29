import pytest

from section_core.assembly import LineToLineJoin
from section_core.components import RectangularElement
from section_core.interfaces import (
    ComponentInterface,
    ContactInterface,
    DuplicateInterfaceError,
    InterfaceReferenceError,
    InvalidInterfaceError,
    WeldInterface,
)
from section_core.section import Section


def _component(element_id: str, y: float = 0.0, z: float = 0.0) -> RectangularElement:
    return RectangularElement.from_bottom_left(
        element_id=element_id,
        width=100,
        width_unit="mm",
        height=20,
        height_unit="mm",
        bottom_left_y=y,
        bottom_left_y_unit="mm",
        bottom_left_z=z,
        bottom_left_z_unit="mm",
    )


def test_component_interface_validation_and_defaults():
    iface = ComponentInterface("IF1", "shared_boundary", "A", "B")
    assert iface.interface_type == "shared_boundary"
    assert iface.verified is False

    with pytest.raises(InvalidInterfaceError, match="Unsupported interface_type"):
        ComponentInterface("IF2", "bad", "A", "B")
    with pytest.raises(InvalidInterfaceError, match="must be different"):
        ComponentInterface("IF3", "contact", "A", "A")
    with pytest.raises(InvalidInterfaceError, match="length_mm must be positive"):
        ComponentInterface("IF4", "contact", "A", "B", length_mm=-1)


def test_weld_interface_validation_and_defaults():
    weld = WeldInterface(interface_id="W1", component_a_id="A", component_b_id="B")
    assert weld.interface_type == "weld"
    assert weld.weld_type == "fillet"
    assert weld.verified is False
    assert weld.structural_action_assumed is False

    with pytest.raises(InvalidInterfaceError, match="weld_size_mm must be positive"):
        WeldInterface(interface_id="W2", component_a_id="A", component_b_id="B", weld_size_mm=0)


def test_contact_interface_defaults():
    contact = ContactInterface(interface_id="C1", component_a_id="A", component_b_id="B")
    assert contact.interface_type == "contact"
    assert contact.contact_type == "bearing"
    assert contact.friction_assumed is False


def test_section_interface_integration():
    section = Section(section_id="SEC", components=[_component("A"), _component("B", y=200)])
    iface = ComponentInterface("IF1", "shared_boundary", "A", "B")
    section.add_interface(iface)
    assert section.interface_ids() == ["IF1"]
    assert section.get_interface("IF1").component_b_id == "B"

    with pytest.raises(DuplicateInterfaceError, match="Duplicate interface_id"):
        section.add_interface(iface)
    with pytest.raises(InterfaceReferenceError, match="missing component_b_id"):
        section.add_interface(ComponentInterface("IF2", "contact", "A", "MISSING"))


def test_line_to_line_connection_interface_creation_behavior():
    target = _component("T1")
    source = _component("S1", y=300)
    section = Section(section_id="SEC", components=[target])

    result_no = LineToLineJoin(
        operation_id="OP-NO",
        operation_type="ignored",
        source_component=source,
        source_line_name="bottom_edge",
        target_component_id="T1",
        target_line_name="top_edge",
        create_connection=False,
    ).apply(section)
    assert result_no.interfaces == []

    result_yes = LineToLineJoin(
        operation_id="OP-YES",
        operation_type="ignored",
        source_component=source,
        source_line_name="bottom_edge",
        target_component_id="T1",
        target_line_name="top_edge",
        create_connection=True,
        interface_type="weld",
        weld_size_mm=6.0,
    ).apply(section)

    assert len(result_yes.interfaces) == 1
    added = result_yes.interfaces[0]
    assert added.component_a_id == "T1"
    assert added.component_b_id == "S1"
    assert added.metadata["created_by_operation_id"] == "OP-YES"
    assert "not structurally verified" in added.metadata["note"]
