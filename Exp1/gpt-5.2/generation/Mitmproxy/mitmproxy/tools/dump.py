from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from mitmproxy.addonmanager import AddonManager, Options


@dataclass
class DumpMaster:
    """
    Minimal DumpMaster compatible with mitmproxy.tools.dump.DumpMaster.
    """
    options: Dict[str, Any] = field(default_factory=dict)
    addons: AddonManager = field(default_factory=AddonManager)
    should_exit: bool = False
    exit_code: int = 0

    def __post_init__(self) -> None:
        # mirror a common pattern: store options object on the addonmanager
        self.addons.options = Options(**self.options)

    def shutdown(self) -> None:
        self.should_exit = True

    def run(self) -> int:
        """
        Simulate running; trigger a couple of lifecycle events if addons exist.
        """
        self.addons.trigger("running")
        self.addons.trigger("done")
        return int(self.exit_code)