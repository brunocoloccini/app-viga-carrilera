"""Assembly operation errors."""


class AssemblyError(ValueError):
    """Base error for section assembly operations."""


class AssemblyReferenceError(AssemblyError):
    """Raised when an assembly operation references unknown components/nodes."""


class AssemblyGeometryError(AssemblyError):
    """Raised when an assembly operation cannot be performed geometrically."""
