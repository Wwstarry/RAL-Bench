class AddonManager:
    """
    Manages addons for mitmproxy, allowing integration of options and commands.
    """
    def __init__(self):
        self.addons = []

    def add(self, addon):
        """
        Add an addon to the manager.
        """
        self.addons.append(addon)

    def remove(self, addon):
        """
        Remove an addon from the manager.
        """
        self.addons.remove(addon)

    def clear(self):
        """
        Remove all addons.
        """
        self.addons.clear()