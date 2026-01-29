"""
Copyright (c) 2006-2024 sqlmap developers (https://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

class _DataContainer(dict):
    """Container class for storing data"""
    def __init__(self):
        super().__init__()
        self.__dict__ = self

# Global data containers
cmdLineOptions = _DataContainer()
conf = _DataContainer()
kb = _DataContainer()