"""
Core data structures for shared runtime state
"""

class _DataContainer:
    """Container for shared data structures"""
    def __init__(self):
        self.cmdLineOptions = None
        self.conf = {}
        self.kb = {}

# Global instances
cmdLineOptions = None
conf = _DataContainer().conf
kb = _DataContainer().kb