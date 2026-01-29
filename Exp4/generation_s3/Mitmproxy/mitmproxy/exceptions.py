from __future__ import annotations


class MitmproxyError(Exception):
    """Base exception for this minimal mitmproxy subset."""


class OptionsError(MitmproxyError):
    """Raised for invalid option values in the minimal options subsystem."""