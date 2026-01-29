from __future__ import annotations

from typing import Iterable, List, Optional, Any


class AddonManager:
    """
    Minimal addon manager.

    Supports add/remove/get/trigger to satisfy tests.
    """

    def __init__(self, master: Optional[object] = None):
        self.master = master
        self.addons: List[object] = []

    def add(self, addon: object) -> None:
        if addon in self.addons:
            return
        self.addons.append(addon)

    def remove(self, addon: object) -> None:
        try:
            self.addons.remove(addon)
        except ValueError:
            return

    def get(self, name: str) -> Optional[object]:
        for a in self.addons:
            addon_name = getattr(a, "name", None)
            if isinstance(addon_name, str) and addon_name == name:
                return a
            if a.__class__.__name__ == name:
                return a
        return None

    def trigger(self, event: str, *args: Any, **kwargs: Any) -> None:
        for a in list(self.addons):
            func = getattr(a, event, None)
            if callable(func):
                func(*args, **kwargs)

    def iter_addons(self) -> Iterable[object]:
        return iter(self.addons)