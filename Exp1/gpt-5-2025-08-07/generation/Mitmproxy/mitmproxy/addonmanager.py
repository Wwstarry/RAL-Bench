"""
Minimal AddonManager.

This module implements a simplified version of mitmproxy's AddonManager that
supports adding/removing addons and triggering hook methods. It also provides
basic options passing for addons at load time.
"""

from __future__ import annotations

from typing import Any, Iterable, List, Optional


class _AddonContext:
    """
    Context object passed to addon load() hooks.

    Attributes:
        options: The options object provided by the master (arbitrary attribute bag).
        addonmanager: A reference back to the addon manager.
    """

    def __init__(self, options: Any, addonmanager: "AddonManager") -> None:
        self.options = options
        self.addonmanager = addonmanager


class AddonManager:
    """
    Manage a set of addons and dispatch lifecycle and event hooks.

    This minimal implementation supports:
      - add(addon): Add an addon and call addon.load(ctx) if present.
      - remove(addon): Remove an addon and call addon.done() if present.
      - trigger(name, *args, **kwargs): Call method "name" on all addons if present.
    """

    def __init__(self, master: Optional[Any] = None) -> None:
        self.master = master
        self._addons: List[Any] = []

    @property
    def options(self) -> Any:
        # Expose master.options if available; else a simple empty object.
        if self.master is not None and hasattr(self.master, "options"):
            return self.master.options
        return type("Options", (), {})()  # Simple empty object

    @property
    def addons(self) -> List[Any]:
        return list(self._addons)

    def add(self, addon: Any) -> None:
        if addon in self._addons:
            return
        self._addons.append(addon)
        load = getattr(addon, "load", None)
        if callable(load):
            ctx = _AddonContext(self.options, self)
            load(ctx)

    # Alias commonly used in addons code.
    register = add

    def add_many(self, addons: Iterable[Any]) -> None:
        for a in addons:
            self.add(a)

    def remove(self, addon: Any) -> None:
        try:
            self._addons.remove(addon)
        except ValueError:
            return
        done = getattr(addon, "done", None)
        if callable(done):
            done()

    def clear(self) -> None:
        # remove all addons, invoking done hooks
        for a in list(self._addons):
            self.remove(a)

    def trigger(self, name: str, *args: Any, **kwargs: Any) -> None:
        """
        Trigger an event hook by name across all addons.
        """
        for addon in list(self._addons):
            fn = getattr(addon, name, None)
            if callable(fn):
                fn(*args, **kwargs)