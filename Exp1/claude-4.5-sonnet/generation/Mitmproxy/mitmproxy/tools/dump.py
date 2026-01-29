"""
mitmdump - a simple HTTP proxy with console output.
"""

from typing import Optional, IO
import sys
from mitmproxy.master import Master
from mitmproxy.options import Options


class DumpMaster(Master):
    """
    DumpMaster is the master for mitmdump, which dumps flows to console/file.
    """
    
    def __init__(self, options: Optional[Options] = None, 
                 outfile: Optional[IO] = None):
        super().__init__(options)
        self.outfile = outfile or sys.stdout
        self._flow_count = 0
        
    def run(self) -> None:
        """
        Run the dump master.
        """
        self.addons.trigger("running")
        
        try:
            # In a real implementation, this would start the proxy server
            # and process flows. For this minimal version, we just trigger
            # the lifecycle events.
            while not self.should_exit:
                break
        except KeyboardInterrupt:
            pass
        finally:
            self.addons.trigger("done")
            
    def log(self, message: str) -> None:
        """
        Log a message to the output file.
        """
        print(message, file=self.outfile)
        
    def dump_flow(self, flow) -> None:
        """
        Dump a flow to the output.
        """
        self._flow_count += 1
        if hasattr(flow, 'request') and flow.request:
            self.log(f"{flow.request.method} {flow.request.url}")
        if hasattr(flow, 'response') and flow.response:
            self.log(f"  <- {flow.response.status_code} {flow.response.reason}")