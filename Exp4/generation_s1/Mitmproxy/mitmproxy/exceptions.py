class MitmproxyError(Exception):
    """Base exception for the minimal mitmproxy subset."""


class OptionsError(MitmproxyError):
    """Raised for invalid options/option operations."""


class CommandError(MitmproxyError):
    """Raised for command manager failures."""