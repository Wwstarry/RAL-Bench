from __future__ import annotations


class GlancesError(Exception):
    """Base error for predictable CLI failures."""


class UnknownFieldError(GlancesError):
    """Raised when an unknown CSV field is requested."""