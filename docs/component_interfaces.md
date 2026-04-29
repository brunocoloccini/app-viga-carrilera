# Component interfaces (V1-011)

Interfaces are modeled separately from geometry so the section model can track construction/connection intent without changing solid topology.

## Supported interface types
- `weld`
- `contact`
- `shared_boundary`
- `construction_joint`
- `bolt_group`

## Notes
- `verified=False` by default for all interfaces.
- `structural_action_assumed` is explicit and defaults to `False`.
- Weld/contact/shared-boundary interfaces are record models only in V1-011.
- No weld strength checks yet.
- No boolean union/topology merge yet.

## Why this matters
This enables traceable modeling for future features:
- CIRSOC J style connection checks,
- fatigue and weld tracking,
- rigidizers and cover-plate connection bookkeeping,
- runway beam/detail assumptions,
- composite-action assumptions.

When created by assembly operations, interface metadata includes operation id, source/target line names, and the note:
`Interface is recorded but not structurally verified.`
