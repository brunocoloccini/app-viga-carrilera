# Crane runway envelope curves (V1-023)

## Purpose

The envelope-curve analysis computes station-based shear and bending moment envelopes for a simple-span runway beam under a moving crane wheel group. Instead of only reporting one global critical value, it gives worst-case values at each station `x` along the span.

## Global envelope vs station envelope curves

- **Global moving-load envelope (V1-022):** tracks critical overall maxima (for example max moment anywhere in the span) for each moving offset.
- **Station-based envelope curves (V1-023):** evaluates `V(x)` and `M(x)` at specified stations and envelopes those station responses over all allowed offsets.

Both analyses use the same moving offset convention and same simple-span statics engine.

## Coordinate and offset conventions

- Station coordinate `x` is measured from the left support, from `0` to `span`.
- Moving offset `offset_x` is the translation applied to the wheel group original x positions.
- Allowed offset range is:
  - `offset_min = -x_min_group`
  - `offset_max = span - x_max_group`

This keeps all wheels within span during each analyzed position.

## Movement and station discretization

- `movement_step` defines the spacing of evaluated moving offsets.
- You may define stations explicitly (`stations=[...]`) or via `station_step`.
- If stations are explicit, they are sorted and deduplicated.
- If `station_step` is used, stations run from 0 to span.
- If neither is provided, default station step is `span/20`.

## Endpoint inclusion

Both analyses include endpoints even when steps do not divide exactly:

- Final moving offset always includes `offset_max`.
- Final station list always includes `span`.

## Scope in V1-023

- Vertical wheel loads only (`include_only_vertical=True` behavior).
- No exact influence-line critical position optimization yet (grid scan only).
- No fatigue extraction.
- No design-code checks (CIRSOC/CISC/AISC).
- No serviceability deflection envelope.
- No lateral/torsional/biaxial stress envelopes.

## Future steps

- Exact critical-position solving (influence-line driven).
- Deflection envelope curves.
- Lateral load envelopes.
- Biaxial stress envelopes.
- Fatigue stress-range extraction.
