"""
The addon manager manages addons - mini-plugins that extend mitmproxy functionality.
"""
from typing import Any, List, Dict, Optional, Callable, Set, Sequence
import types


class Loader:
    """
    A loader object that manages loading addons.
    """
    def __init__(self, master):
        self.master = master

    def load_file(self, path):
        """Load a file as an addon."""
        pass


class AddonManager:
    """
    Manages addon loading and lifecycle.
    """
    def __init__(self, master):
        self.master = master
        self.addons = []
        self.loader = Loader(master)
    
    def clear(self):
        """
        Remove all addons.
        """
        self.addons = []

    def register(self, addon):
        """
        Register an addon to be managed.
        """
        self.addons.append(addon)

    def add(self, *addons):
        """
        Add addons to the manager. This will also register events automatically.
        """
        for addon in addons:
            self.register(addon)

    def remove(self, addon):
        """
        Remove an addon from being managed.
        """
        if addon in self.addons:
            self.addons.remove(addon)
            
    def trigger(self, event_name, *args, **kwargs):
        """
        Trigger an event on all registered addons.
        """
        for addon in self.addons:
            func = getattr(addon, event_name, None)
            if func:
                func(*args, **kwargs)