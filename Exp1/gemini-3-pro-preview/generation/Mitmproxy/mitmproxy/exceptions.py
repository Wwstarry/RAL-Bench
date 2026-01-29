class MitmproxyException(Exception):
    """Base class for all mitmproxy exceptions."""
    pass

class FlowReadException(MitmproxyException):
    pass

class ControlException(MitmproxyException):
    pass

class OptionsError(MitmproxyException):
    pass

class AddonError(MitmproxyException):
    pass