# Shape library JSON import/export

This document describes JSON import/export support for tabulated shape libraries in `section_core`.

## Purpose

The JSON I/O layer allows loading and saving shape tables with explicit units per quantity. This keeps the package UI-independent and enables deterministic tests and data exchange.

## Expected structure

A library JSON object contains metadata and a `records` list:

- `library_id`, `name`, `source`, `version`, `unit_system`, `description`
- `records`: list of shape records

Each record includes:

- `shape_id`, `shape_family`, `shape_name`, `source`
- required explicit quantity objects: `depth`, `width`, `area`, `Iyy`, `Izz`
- optional explicit quantity objects: `Iyz`, `J`, `Cw`
- `metadata` for extra annotations

Each quantity object uses:

- `value`: numeric value
- `unit`: explicit unit string (for example `mm`, `cm2`, `mm4`, `cm6`)

## Unit handling

`registry_from_json_dict` builds `ShapeRecord` instances using `ShapeRecord.from_values`, so unit conversion and dimensional compatibility are validated in one place.

Examples:

- `area` in `cm2` converts to internal `mm2`
- `Iyy`/`Izz` in `cm4` converts to internal `mm4`
- `Cw` in `cm6` converts to internal `mm6`
- invalid dimensional units (for example `Cw` with `cm4`) are rejected

## Why real profile data is not included yet

This milestone adds robust mechanics for file format + validation only. It intentionally does **not** include full official shape databases.

This prepares the repository for future additions such as:

- CIRSOC W/IPE/IPN/UPN tables
- AISC W-shape libraries
- CISC W-shape libraries
- user-defined custom libraries

## Current limitations

- no PDF extraction/scraping
- no full official profile database
- no design-code classification/check logic
- no automatic validation against official published tables
