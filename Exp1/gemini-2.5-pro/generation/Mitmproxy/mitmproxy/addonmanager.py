import typing

class AddonManager:
    """
    A stub for mitmproxy's addon manager.

    This class is responsible for loading and managing addons, and for
    triggering events. For this minimal implementation, it only keeps
    track of loaded addons and provides no-op event triggering.
    """
    def __init__(self, master):
        self.master = master
        self.addons: typing.List[typing.Any] = []

    def load(self, addon: typing.Any):
        """
        Loads an addon. In this stub, it just adds the addon to a list.
        """
        self.addons.append(addon)
        self._configure_addon(addon)

    def _configure_addon(self, addon: typing.Any):
        """
        Placeholder for addon configuration logic.
        """
        if hasattr(addon, "load"):
            addon.load(self)
        if hasattr(addon, "running"):
            self.master.events.on("running", addon.running)

    def trigger(self, event: str, *args, **kwargs):
        """
        Triggers an event on all loaded addons.

        In a real implementation, this would invoke methods on addons that
        correspond to the event name. For this stub, it does nothing.
        """
        pass

    def done(self):
        """
        Called when the addon manager is shutting down. Triggers the 'done' event.
        """
        self.trigger("done")