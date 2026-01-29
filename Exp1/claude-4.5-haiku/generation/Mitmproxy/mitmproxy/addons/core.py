"""
Core addon providing fundamental functionality.
"""

from typing import Any


class Core:
    """
    Core addon with essential mitmproxy functionality.
    """
    
    def __init__(self):
        self.name = "core"
    
    def load(self, loader: Any) -> None:
        """
        Load the core addon.
        
        Args:
            loader: Addon loader/manager
        """
        pass
    
    def done(self) -> None:
        """
        Called when mitmproxy is shutting down.
        """
        pass