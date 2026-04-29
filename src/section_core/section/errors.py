"""Section errors."""


class SectionError(ValueError):
    """Base error for section container operations."""


class EmptySectionError(SectionError):
    """Raised when section properties are requested for an empty section."""


class DuplicateComponentError(SectionError):
    """Raised when adding a component with duplicate element_id."""


class UnsupportedComponentTypeError(SectionError):
    """Raised when a component type is unsupported for current calculations."""


class InvalidSectionPropertiesError(SectionError):
    """Raised when derived section properties are invalid."""
