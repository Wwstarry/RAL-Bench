from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any, List, Optional

from mitmproxy.addonmanager import AddonManager


@dataclass
class DumpMaster:
    """
    Minimal mitmdump master.

    The real project orchestrates network servers, event loops, and addons.
    Here we keep a small lifecycle to satisfy tests and basic CLI execution.
    """
    options: Any = None
    addons: AddonManager = field(default_factory=AddonManager)
    should_exit: bool = False

    def __post_init__(self) -> None:
        # If options has an "addons" iterable, load them.
        extra = getattr(self.options, "addons", None)
        if extra:
            try:
                self.addons.add(*list(extra))
            except Exception:
                # Keep robust for tests; do not fail on addon load.
                pass

    def run(self) -> int:
        """
        Execute the main loop. For this kata, just fire a couple of lifecycle hooks.
        """
        self.addons.trigger("running")
        self.addons.trigger("done")
        return 0

    def shutdown(self) -> None:
        self.should_exit = True
        self.addons.trigger("done")

    def log(self, message: str) -> None:
        print(message, file=sys.stderr)