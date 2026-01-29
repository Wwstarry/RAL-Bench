"""
Minimal subset of mitmproxy.addonmanager for testing.
"""

class AddonManager:
    """
    Represents a minimal AddonManager placeholder.
    """

    def __init__(self):
        self.addons = []

    def add(self, addon):
        self.addons.append(addon)

    def remove(self, addon):
        self.addons.remove(addon)

    def clear(self):
        self.addons.clear()