# Crane runway user-facing error formatting (V1-040)

## Purpose
This module provides user-facing validation reports for crane runway case JSON files. It converts low-level schema and case execution errors into structured messages suitable for future UI/API layers.

## Relationship to existing modules
- `case_schema.py` still owns schema validation logic.
- `case_io.py` still owns case-file loading/conversion/execution.
- `error_formatting.py` wraps those outcomes into deterministic `UserFacingValidationReport` objects.

## Message structure
`UserFacingValidationMessage` includes:
- `path`
- `message`
- `severity` (`error`, `warning`, `info`)
- optional `code`
- optional `hint`
- optional `metadata`

## Severity levels
- `error`: blocks case usage.
- `warning`: non-blocking issue.
- `info`: informational detail.

## Error codes
Stable codes used by formatter:
- `CASE_SCHEMA_ERROR`
- `CASE_JSON_ERROR`
- `CASE_IO_ERROR`
- `CASE_EXECUTION_ERROR`
- `CASE_UNKNOWN_ERROR`

## Hints
The formatter adds deterministic hints for common patterns such as:
- missing `schema_version`
- missing quantity `unit`
- unsupported serviceability/stress limit types
- duplicate `wheel_id`
- rail eccentricity include flags both false

## Output forms
- `to_text()`: readable multiline output with severity/path and hint lines.
- `to_dict()`: JSON-serializable dictionary for API payloads.

## Future UI/API use
This layer keeps domain validation and end-user presentation concerns separate, allowing APIs/UIs to consume one stable report format.

## Limitations
- Not a UI.
- No localization/i18n yet.
- Not a full external JSON Schema validator.
- Does not run structural checks by itself.
