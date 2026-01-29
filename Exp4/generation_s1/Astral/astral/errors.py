class AstralError(ValueError):
    """Base error for Astral-like calculations.

    Subclasses ValueError to stay compatible with code that expects ValueError.
    """


class SunNeverRisesError(AstralError):
    """Raised when the sun never rises (for the given observer/date/elevation)."""


class SunNeverSetsError(AstralError):
    """Raised when the sun never sets (for the given observer/date/elevation)."""