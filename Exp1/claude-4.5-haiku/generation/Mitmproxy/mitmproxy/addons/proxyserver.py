"""
Proxy server addon.
"""

from typing import Any


class Proxyserver:
    """
    Addon that manages the proxy server.
    """
    
    def __init__(self):
        self.name = "proxyserver"
    
    def load(self, loader: Any) -> None:
        """
        Load the proxyserver addon.
        
        Args:
            loader: Addon loader/manager
        """
        pass
    
    def done(self) -> None:
        """
        Called when mitmproxy is shutting down.
        """
        pass