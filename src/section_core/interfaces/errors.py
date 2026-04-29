"""Interface modeling errors."""


class InterfaceError(ValueError):
    """Base error for interface modeling."""


class InvalidInterfaceError(InterfaceError):
    """Raised when interface fields are invalid."""


class InterfaceReferenceError(InterfaceError):
    """Raised when interface references unknown components."""


class DuplicateInterfaceError(InterfaceError):
    """Raised when interface_id is duplicated within a section."""
