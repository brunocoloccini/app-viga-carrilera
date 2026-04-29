"""Geometry and coordinate frame errors."""


class GeometryError(Exception):
    """Base class for geometry-related errors."""


class CoordinateFrameError(GeometryError):
    """Base class for coordinate-frame errors."""


class UnsupportedCoordinateFrameError(CoordinateFrameError):
    """Raised when a requested frame behavior is not implemented."""


class InvalidToleranceError(GeometryError):
    """Raised when geometric tolerance settings are invalid."""


class DegenerateGeometryError(GeometryError):
    """Raised when a geometric entity is degenerate."""


class GeometryMergeError(GeometryError):
    """Raised when a requested geometry merge is not possible."""
