"""Crane runway load-model errors."""


class CraneRunwayError(ValueError):
    """Base error for crane runway load modeling."""


class InvalidWheelLoadError(CraneRunwayError):
    """Invalid wheel load definition or units."""


class InvalidCraneLoadModelError(CraneRunwayError):
    """Invalid crane load model factors or identifiers."""


class DuplicateWheelError(CraneRunwayError):
    """Duplicate wheel identifiers inside one wheel group."""
