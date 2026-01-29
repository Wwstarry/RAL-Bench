from mitmproxy.addonmanager import AddonManager
from mitmproxy.options import Options
from mitmproxy import ctx

class Master:
    """
    The master handles addons and options.
    """
    def __init__(self, options: Options):
        self.options = options or Options()
        self.addons = AddonManager(self)
        self.log = None
        # Set global context
        ctx.master = self

    def run(self):
        self.addons.trigger("running")
        try:
            # In a real implementation, this would start the event loop
            pass
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def shutdown(self):
        self.addons.trigger("done")