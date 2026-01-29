"""
Extremely stripped-down representation of mitmproxy's *AddonManager*.

The original implementation deals with the plug-in life-cycle, command
registration, options management, …  
For the purpose of CLI/help tests we only need to support
`register()`/`unregister()` and an *additive* `addons` set.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Iterable, List


class AddonManager:
    """
    Manage a collection of addon instances.

    The real mitmproxy offers event broadcasting, dynamic command
    dispatching and much more.  This is **only** a façade that fulfils
    the import/attribute requirements of the public test-suite.
    """

    def __init__(self, options: Any | None = None) -> None:
        # Store the options object as is – could be an argparse.Namespace
        # or a plain dict.  We never inspect its attributes within the
        # stub.
        self.options = options if options is not None else SimpleNamespace()
        self.addons: List[Any] = []

    # ------------------------------------------------------------------
    # Public helpers – these *do nothing* but are required to exist.
    # ------------------------------------------------------------------
    def register(self, addon: Any) -> None:
        """Add *addon* to the internal registry."""
        if addon not in self.addons:
            self.addons.append(addon)

    def unregister(self, addon: Any) -> None:
        """Remove *addon* from the registry (silently ignore missing)."""
        try:
            self.addons.remove(addon)
        except ValueError:
            pass

    # The test-suite might iterate over the manager, so let's make it
    # possible.
    def __iter__(self) -> Iterable[Any]:
        return iter(self.addons)

    # A decent string representation is always handy.
    def __repr__(self) -> str:  # noqa: D401
        return f"<AddonManager {len(self.addons)} addons>"