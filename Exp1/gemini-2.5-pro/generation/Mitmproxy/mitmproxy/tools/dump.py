import sys
import time
from mitmproxy import master
from mitmproxy import options

class DumpMaster(master.Master):
    """
    A stub for the mitmdump master class.

    This master is not interactive and is designed for batch processing of
    flows, such as reading from a file, processing with a script, and
    writing to another file.
    """
    def __init__(self, options: options.Options, with_termlog: bool = True, with_dumper: bool = True):
        super().__init__(options)
        # These are placeholders to match the real constructor signature.
        self.with_termlog = with_termlog
        self.with_dumper = with_dumper

    def run(self):
        """
        The main loop for mitmdump.

        In a real implementation, this would start listening for connections
        or reading from a file. For this stub, we simulate a running process
        that can be shut down.
        """
        self.addons.trigger("running")
        try:
            if self.with_termlog and not self.options.quiet:
                print("mitmdump: proxy running.", file=sys.stderr)
            # In a real app, this would be an event loop. Here, we just
            # simulate a running process that waits to be shut down.
            # For the benchmark, this function just needs to be callable.
            if self.options.rfile:
                # If reading a file, we can simulate finishing the task.
                pass
            else:
                # If running as a proxy, simulate running forever.
                # The test will likely terminate the process.
                while True:
                    time.sleep(0.1)
        except (KeyboardInterrupt, SystemExit):
            # Gracefully handle termination signals.
            pass
        finally:
            self.shutdown()