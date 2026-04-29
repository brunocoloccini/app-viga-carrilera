"""Custom errors for units subsystem."""


class UnitError(ValueError):
    """Base error for unit parsing or conversion issues."""


class UnitCompatibilityError(UnitError):
    """Raised when a unit does not match expected dimension."""
