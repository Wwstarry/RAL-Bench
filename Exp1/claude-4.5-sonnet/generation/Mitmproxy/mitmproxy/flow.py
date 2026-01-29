"""
Flow base abstractions for mitmproxy.
"""

from typing import Optional, Any, Dict


class Flow:
    """
    Base class for all flows.
    A flow is a collection of objects representing a single transaction.
    """
    
    def __init__(self):
        self.id: Optional[str] = None
        self.error: Optional[Any] = None
        self.intercepted: bool = False
        self.marked: bool = False
        self.metadata: Dict[str, Any] = {}
        self.comment: str = ""
        self.live: bool = True
        
    def copy(self) -> "Flow":
        """Create a copy of this flow."""
        new_flow = self.__class__()
        new_flow.id = self.id
        new_flow.error = self.error
        new_flow.intercepted = self.intercepted
        new_flow.marked = self.marked
        new_flow.metadata = self.metadata.copy()
        new_flow.comment = self.comment
        new_flow.live = self.live
        return new_flow
        
    def kill(self) -> None:
        """Kill this flow."""
        self.live = False
        
    def resume(self) -> None:
        """Resume this flow if intercepted."""
        self.intercepted = False