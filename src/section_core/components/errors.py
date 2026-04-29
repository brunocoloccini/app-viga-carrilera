"""Component-specific errors."""


class ComponentError(ValueError):
    """Base error for section components."""


class InvalidComponentGeometryError(ComponentError):
    """Raised when component geometry is invalid."""


class UnsupportedComponentOperationError(ComponentError):
    """Raised when an unsupported operation is requested."""


class UnknownReferenceError(ComponentError):
    """Raised when a named node/point/line reference does not exist."""
