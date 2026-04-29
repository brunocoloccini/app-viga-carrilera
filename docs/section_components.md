# Section components (V1-004)

`SectionElement` is the base geometric primitive owned by a future section model. It carries identity (`element_id`), type (`element_type`), provenance (`source`), and optional material/metadata.

`RectangularElement` represents a rectangle in the section **Y-Z** plane:
- **y**: horizontal axis
- **z**: vertical axis
- internal storage in **mm**

It provides stable named nodes/reference points (`bottom_left`, `top_right`, `center`, edge midpoints) and named reference lines (`top_edge`, `bottom_edge`, `left_edge`, `right_edge`).

`PlateElement` is a semantic rectangle specialization with `element_type="plate"`, plus plate-specific intent (`orientation`, `thickness_internal_mm`).

In V1-004 components are geometric-only primitives; they are not yet a full `Section` container and do not compute global section properties.

These primitives are intended for future composition/assembly operations such as node-to-node, node-to-point, and line-to-line matching/constraints.
