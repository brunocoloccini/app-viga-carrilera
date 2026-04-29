"""Errors for shape library registry."""


class ShapeLibraryError(Exception):
    """Base error for shape library operations."""


class DuplicateShapeError(ShapeLibraryError):
    """Raised when attempting to register a duplicate shape id."""


class ShapeNotFoundError(ShapeLibraryError):
    """Raised when a requested shape does not exist in the registry."""


class InvalidShapeRecordError(ShapeLibraryError):
    """Raised when a shape record is invalid."""
