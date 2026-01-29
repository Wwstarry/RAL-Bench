"""
Master class - the core controller for mitmproxy.
"""

from typing import Optional, Any
from mitmproxy.addonmanager import AddonManager
from mitmproxy.options import Options


class Master:
    """
    The master handles the proxy server and the flow of events.
    """
    
    def __init__(self, options: Optional[Options] = None):
        self.options = options or Options()
        self.addons = AddonManager(self)
        self.should_exit = False
        self.server: Optional[Any] = None
        
    def run(self) -> None:
        """
        Run the master event loop.
        """
        self.addons.trigger("running")
        
        try:
            while not self.should_exit:
                # Main event loop would go here
                # For this minimal implementation, we just break
                break
        finally:
            self.addons.trigger("done")
            
    def shutdown(self) -> None:
        """
        Shutdown the master.
        """
        self.should_exit = True
        
    def load_flow(self, flow) -> None:
        """
        Load a flow into the master.
        """
        self.addons.trigger("flow_created", flow)