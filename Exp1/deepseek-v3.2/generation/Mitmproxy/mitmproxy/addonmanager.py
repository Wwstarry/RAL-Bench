"""
AddonManager for options/commands integration.
"""

from typing import Any, Dict, List, Optional, Callable
import dataclasses


@dataclasses.dataclass
class Loader:
    """Addon loader context."""
    master: Any


class AddonManager:
    """Manages addons and their options/commands."""
    
    def __init__(self, master: Any) -> None:
        self.master = master
        self.addons: List[Any] = []
    
    def add(self, addon: Any) -> None:
        """Add an addon."""
        self.addons.append(addon)
        if hasattr(addon, 'load'):
            addon.load(Loader(self.master))
    
    def remove(self, addon: Any) -> None:
        """Remove an addon."""
        if addon in self.addons:
            if hasattr(addon, 'done'):
                addon.done()
            self.addons.remove(addon)
    
    def trigger(self, event: str, *args, **kwargs) -> None:
        """Trigger an event on all addons."""
        for addon in self.addons:
            method = getattr(addon, event, None)
            if callable(method):
                method(*args, **kwargs)