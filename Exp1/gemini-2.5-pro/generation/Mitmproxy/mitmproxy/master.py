from mitmproxy import addonmanager
from mitmproxy import options

class Master:
    """
    A stub for the base Master class.
    The master is the central coordinating object in mitmproxy.
    """
    def __init__(self, opts: options.Options):
        self.options = opts
        self.addons = addonmanager.AddonManager(self)
        # A simple event bus mock
        self.events = type("Events", (), {"on": lambda s, n, f: None})()


    def run(self):
        """
        The main loop of the master. This method is meant to be overridden.
        """
        raise NotImplementedError()

    def shutdown(self):
        """
        Shutdown the master and its addons.
        """
        self.addons.done()