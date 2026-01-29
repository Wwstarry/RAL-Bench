"""
DumpMaster for mitmdump frontend.
"""

from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class DumpMasterOptions:
    """Options for DumpMaster."""
    listen_host: str = "127.0.0.1"
    listen_port: int = 8080
    mode: str = "regular"
    verbose: bool = False
    quiet: bool = False
    flow_detail: int = 2


class DumpMaster:
    """
    Master class for mitmdump frontend.
    
    Handles HTTP interception and dumping to console.
    """
    
    def __init__(self, options: Any = None):
        """
        Initialize DumpMaster.
        
        Args:
            options: Configuration options object
        """
        if options is None:
            options = DumpMasterOptions()
        
        self.options = options
        self.running = False
    
    def run(self) -> None:
        """
        Run the dump master.
        """
        self.running = True
        # Minimal implementation - just exit cleanly
        self.running = False
    
    def shutdown(self) -> None:
        """
        Shutdown the dump master.
        """
        self.running = False