# Units module

The units module provides:
- explicit dimension categories;
- unit registry and conversion factors;
- quantity parsing with strict dimensional validation;
- canonical internal units for deterministic numerical operations.

Current canonical internal units are SI-oriented:
- length: `mm`
- area: `mm2`
- inertia: `mm4`
- warping constant: `mm6`
- section modulus: `mm3`
- force: `N`
- moment: `Nmm`
- stress: `MPa`
- mass: `kg`
- line force: `N/mm`
- mass per length: `kg/m`
- dimensionless: `-`

For warping constant values (e.g., `Cw` in profile tables), CIRSOC-style tabulated inputs in `cm6` are supported and converted to internal `mm6`.
