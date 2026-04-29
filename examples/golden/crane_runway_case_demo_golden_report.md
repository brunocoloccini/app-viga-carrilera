# Crane Runway Demand Summary

## Identification
| Field | Value |
|---|---|
| summary_id | demo_case |
| section_id | ipn_200_with_cover_plate |
| load_model_id | demo_crane |

## Demands
| Demand | Value |
|---|---|
| Span | 6.000 m |
| Max vertical moment | 208.333 kN·m |
| Max vertical shear | 166.667 kN |
| Max vertical deflection | 118.724 mm |
| Max lateral moment | 16.667 kN·m |
| Max biaxial stress | 1182.856 MPa |
| Max torsional input | 3.300 kN·m |

## Checks
| Check | Status |
|---|---|
| Serviceability | FAIL |
| Stress criteria | FAIL |
| Overall | FAIL |

### Serviceability details
| Check ID | Limit ID | Demand | Allowable | Utilization | Status |
|---|---|---:|---:|---:|---|
| moving:L_over_600 | L_over_600 | N/A | N/A | N/A | FAIL |

### Stress utilization details
| Check ID | Limit ID | Demand | Allowable | Utilization | Critical Point | Status |
|---|---|---:|---:|---:|---|---|
| biaxial:0.66Fy | 0.66Fy | N/A | N/A | N/A | bottom_left | FAIL |

## Warnings
- CIRSOC sample profile data is manually curated and must be independently verified before production use.
- No CIRSOC design-code checks are performed.
- Lateral wheel group translated to representative vertical critical offset for lateral analysis.