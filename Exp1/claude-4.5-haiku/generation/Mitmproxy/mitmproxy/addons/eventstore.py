"""
Event store addon for flow history.
"""

from typing import Any, List
from mitmproxy.flow import Flow


class EventStore:
    """
    Addon that stores flows and events.
    """
    
    def __init__(self):
        self.name = "eventstore"
        self.flows: List[Flow] = []
    
    def load(self, loader: Any) -> None:
        """
        Load the eventstore addon.
        
        Args:
            loader: Addon loader/manager
        """
        pass
    
    def request(self, flow: Any) -> None:
        """
        Called when a request is received.
        
        Args:
            flow: The HTTP flow
        """
        pass
    
    def response(self, flow: Any) -> None:
        """
        Called when a response is received.
        
        Args:
            flow: The HTTP flow
        """
        pass