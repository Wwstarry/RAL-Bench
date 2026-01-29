"""
Proxy server implementation.
"""

from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class ProxyServer:
    """
    Minimal proxy server implementation.
    """
    host: str = "127.0.0.1"
    port: int = 8080
    
    def start(self) -> None:
        """Start the proxy server."""
        pass
    
    def stop(self) -> None:
        """Stop the proxy server."""
        pass