"""Geometry and coordinate frame errors."""


class GeometryError(Exception):
    """Base class for geometry-related errors."""


class CoordinateFrameError(GeometryError):
    """Base class for coordinate-frame errors."""


class UnsupportedCoordinateFrameError(CoordinateFrameError):
    """Raised when a requested frame behavior is not implemented."""
