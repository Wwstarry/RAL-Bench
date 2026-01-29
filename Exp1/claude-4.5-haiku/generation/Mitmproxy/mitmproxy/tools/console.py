"""
Console UI frontend for mitmproxy.
"""

from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class ConsoleOptions:
    """Options for console."""
    listen_host: str = "127.0.0.1"
    listen_port: int = 8080
    mode: str = "regular"
    verbose: bool = False


class ConsoleMaster:
    """
    Master class for mitmproxy console UI.
    
    Provides an interactive terminal-based UI.
    """
    
    def __init__(self, options: Any = None):
        """
        Initialize ConsoleMaster.
        
        Args:
            options: Configuration options object
        """
        if options is None:
            options = ConsoleOptions()
        
        self.options = options
        self.running = False
    
    def run(self) -> None:
        """
        Run the console master.
        """
        self.running = True
        self.running = False
    
    def shutdown(self) -> None:
        """
        Shutdown the console master.
        """
        self.running = False