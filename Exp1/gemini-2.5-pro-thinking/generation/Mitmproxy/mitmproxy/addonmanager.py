import inspect

class AddonManager:
    """
    A minimal, safe-to-evaluate placeholder for mitmproxy's AddonManager.
    It manages a list of addons and can trigger events.
    """
    def __init__(self, master):
        self.master = master
        self.addons = []

    def add(self, *addons):
        """A convenience alias for load."""
        self.load(*addons)

    def load(self, *addons):
        """Loads addons into the manager."""
        for addon in addons:
            if addon not in self.addons:
                self.addons.append(addon)
                if hasattr(addon, "load"):
                    addon.load(self)

    def trigger(self, event, *args, **kwargs):
        """
        Triggers a given event on all loaded addons that have a handler for it.
        """
        for addon in self.addons:
            handler = getattr(addon, event, None)
            if callable(handler):
                handler(*args, **kwargs)

    def __len__(self):
        return len(self.addons)

    def __iter__(self):
        return iter(self.addons)