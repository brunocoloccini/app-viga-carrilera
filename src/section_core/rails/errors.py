"""Errors for crane rail records and registries."""


class RailLibraryError(Exception):
    """Base error for crane rail library operations."""


class InvalidRailRecordError(RailLibraryError):
    """Raised when a crane rail record is invalid."""


class DuplicateRailRecordError(RailLibraryError):
    """Raised when a duplicate crane rail id is inserted."""


class RailRecordNotFoundError(RailLibraryError):
    """Raised when a crane rail id does not exist in the registry."""
