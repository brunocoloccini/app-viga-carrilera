# Section basic gross elastic properties (V1-005)

`Section` represents a collection of section components in the **Y-Z plane**.

## Component vs section

- A **component** is an individual geometric part (for V1-005: `RectangularElement` and `PlateElement`).
- A **section** is the aggregate container used for global gross property calculations.

## Gross area

The section gross area is the algebraic sum of component areas:

\[
A = \sum_i A_i
\]

For rectangles/plates:

\[
A_i = b_i h_i
\]

## Gross centroid

\[
y_c = \frac{\sum_i A_i y_i}{\sum_i A_i}, \quad
z_c = \frac{\sum_i A_i z_i}{\sum_i A_i}
\]

## Inertia convention

- `y` = horizontal axis
- `z` = vertical axis
- `Iyy` = inertia about horizontal `y` axis
- `Izz` = inertia about vertical `z` axis
- `Iyz` = product of inertia

For unrotated rectangular components:

\[
I_{yy,local} = \frac{b h^3}{12},\quad
I_{zz,local} = \frac{h b^3}{12},\quad
I_{yz,local}=0
\]

Using parallel-axis theorem:

\[
I_{yy} = \sum_i (I_{yy,i} + A_i \Delta z_i^2),\quad
I_{zz} = \sum_i (I_{zz,i} + A_i \Delta y_i^2),\quad
I_{yz} = \sum_i (I_{yz,i} + A_i \Delta y_i \Delta z_i)
\]

## Section modulus convention

\[
S_{y,top}=\frac{I_{yy}}{z_{max}-z_c},\
S_{y,bottom}=\frac{I_{yy}}{z_c-z_{min}},\
S_{z,left}=\frac{I_{zz}}{y_c-y_{min}},\
S_{z,right}=\frac{I_{zz}}{y_{max}-y_c}
\]

Denominators must be strictly positive.

## Traceability

`gross_elastic_properties()` returns a trace list with per-component:

- component id
- area
- centroid coordinates
- local inertias
- offsets to section centroid
- contributions to global inertias

## Current limitations (V1-005)

- **No overlap subtraction** between components.
- `overlap_check_status` is always `"not_implemented"`.
- Only unrotated `RectangularElement` and `PlateElement` are supported.
- No plastic properties.
- No torsional properties.
- No shear center.
- No section classification/check code logic (including CIRSOC).
