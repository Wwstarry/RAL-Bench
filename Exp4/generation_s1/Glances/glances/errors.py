class GlancesError(Exception):
    """Base error for this minimal glances implementation."""


class UsageError(GlancesError):
    """Raised for invalid user input/usage."""


class UnknownFieldError(GlancesError):
    """Raised when unknown CSV fields are requested."""