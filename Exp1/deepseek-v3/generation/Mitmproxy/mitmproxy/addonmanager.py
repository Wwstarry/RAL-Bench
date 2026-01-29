"""AddonManager for options/commands integration"""

from typing import List, Dict, Any, Optional

class AddonManager:
    def __init__(self, master):
        self.master = master
        self.addons: List[Any] = []
    
    def add(self, addon) -> None:
        """Add an addon to the manager"""
        self.addons.append(addon)
    
    def remove(self, addon) -> None:
        """Remove an addon from the manager"""
        if addon in self.addons:
            self.addons.remove(addon)
    
    def get(self, name: str) -> Optional[Any]:
        """Get an addon by name"""
        for addon in self.addons:
            if getattr(addon, 'name', None) == name:
                return addon
        return None