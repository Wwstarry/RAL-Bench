"""
Flow base abstractions.
"""

from typing import Optional, Dict, Any
import dataclasses


@dataclasses.dataclass
class Flow:
    """Base class for all flows."""
    id: str = ""
    client_conn: Optional[dict] = None
    server_conn: Optional[dict] = None
    error: Optional[dict] = None
    intercepted: bool = False
    type: str = "base"
    
    def kill(self) -> None:
        """Kill this flow."""
        self.error = {"msg": "killed"}
    
    def backup(self) -> None:
        """Create a backup of the current flow state."""
        pass
    
    def revert(self) -> None:
        """Revert to the last backup."""
        pass