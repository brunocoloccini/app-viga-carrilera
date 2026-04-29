"""Material model errors."""


class MaterialError(Exception):
    """Base material error."""


class InvalidMaterialError(MaterialError):
    """Raised when material data is invalid."""
