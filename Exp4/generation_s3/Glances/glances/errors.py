from __future__ import annotations


class GlancesError(Exception):
    """Base error for predictable CLI failures."""


class UsageError(GlancesError):
    """Raised for invalid user input not handled by argparse."""


class UnknownFieldError(GlancesError):
    """Raised when a requested CSV field is not supported."""