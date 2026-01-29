"""
Minimal mitmdump master implementation.

DumpMaster is a very small orchestration class sufficient for importability
and basic option handling in tests. It does not start any servers or perform I/O.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from ..addonmanager import AddonManager
from ..options import Options


class DumpMaster:
    """
    Minimal DumpMaster.

    Attributes:
        options: Options object.
        addons: AddonManager to manage addons.
    """

    def __init__(
        self,
        options: Optional[Options] = None,
        with_termlog: bool = True,
        with_dumper: bool = True,
    ) -> None:
        self.options: Options = options if options is not None else Options()
        self.addons: AddonManager = AddonManager(master=self)
        self._running: bool = False
        # Placeholders for compatibility
        self.with_termlog = with_termlog
        self.with_dumper = with_dumper

    def add_addons(self, addons: Iterable[Any]) -> None:
        self.addons.add_many(addons)

    def run(self) -> int:
        """
        No-op run loop; returns 0 immediately to avoid any side effects.
        """
        self._running = True
        # In the real tool, this would start the event loop and proxy machinery.
        # Here, we do nothing for safety and determinism.
        self._running = False
        return 0

    def shutdown(self) -> None:
        self._running = False
        # Let addons clean up
        self.addons.clear()

    def __enter__(self) -> "DumpMaster":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.shutdown()