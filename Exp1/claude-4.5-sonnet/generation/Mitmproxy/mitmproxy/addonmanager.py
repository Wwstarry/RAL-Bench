"""
Addon management for mitmproxy.
"""

from typing import List, Any, Optional, Dict


class AddonManager:
    """
    Manages addons and their lifecycle.
    """
    
    def __init__(self, master):
        self.master = master
        self.addons: List[Any] = []
        self.chain: List[Any] = []
        
    def add(self, *addons) -> None:
        """
        Add addons to the manager.
        """
        for addon in addons:
            if addon not in self.addons:
                self.addons.append(addon)
                self.chain.append(addon)
                
    def remove(self, addon) -> None:
        """
        Remove an addon from the manager.
        """
        if addon in self.addons:
            self.addons.remove(addon)
        if addon in self.chain:
            self.chain.remove(addon)
            
    def trigger(self, event: str, *args, **kwargs) -> None:
        """
        Trigger an event on all addons.
        """
        for addon in self.chain:
            if hasattr(addon, event):
                getattr(addon, event)(*args, **kwargs)
                
    def __len__(self) -> int:
        return len(self.addons)
        
    def __iter__(self):
        return iter(self.addons)