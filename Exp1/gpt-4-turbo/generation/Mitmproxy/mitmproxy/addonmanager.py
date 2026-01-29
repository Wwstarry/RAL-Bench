# Minimal mitmproxy.addonmanager API surface

from typing import List, Any


class AddonManager:
    def __init__(self):
        self.addons: List[Any] = []

    def add(self, addon: Any):
        self.addons.append(addon)

    def remove(self, addon: Any):
        if addon in self.addons:
            self.addons.remove(addon)

    def trigger(self, event: str, *args, **kwargs):
        for addon in self.addons:
            handler = getattr(addon, event, None)
            if callable(handler):
                handler(*args, **kwargs)