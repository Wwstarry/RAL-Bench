"""
mitmdump is a command-line interface for mitmproxy.
"""
from typing import Optional, Sequence
import signal
import sys


class DumpMaster:
    """
    Master class for mitmdump.
    """
    def __init__(self, options=None):
        from mitmproxy.addonmanager import AddonManager
        
        self.options = options or {}
        self.addons = AddonManager(self)
        self.shutdown_requested = False

    def run(self) -> None:
        """
        Run the master.
        """
        self.addons.trigger("running")
        try:
            while not self.shutdown_requested:
                # This would be where actual proxy handling occurs
                # For safety, we just break immediately
                break
        except KeyboardInterrupt:
            pass
        self.shutdown()

    def shutdown(self) -> None:
        """
        Shutdown the master.
        """
        self.addons.trigger("done")