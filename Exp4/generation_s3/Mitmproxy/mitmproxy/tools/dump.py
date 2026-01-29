from __future__ import annotations

from typing import Optional

from mitmproxy.addonmanager import AddonManager
from mitmproxy.options import Options
from mitmproxy import ctx


class DumpMaster:
    """
    Minimal orchestration stub for mitmdump.

    The real mitmproxy starts network servers, event loops, addons, etc.
    This stub is safe: it does nothing besides toggling a running flag.
    """

    def __init__(self, options: Optional[object] = None, *, with_termlog: bool = True, with_dumper: bool = True):
        self.options = options if options is not None else Options()
        self.addons = AddonManager(master=self)
        self.running = False
        self.with_termlog = bool(with_termlog)
        self.with_dumper = bool(with_dumper)

        # Provide minimal ctx integration commonly relied on by addons.
        ctx.ctx.master = self
        ctx.ctx.options = self.options

    def run(self) -> None:
        # No blocking, no sockets.
        self.running = True
        # Trigger minimal lifecycle events if addons were attached.
        self.addons.trigger("load", self)
        self.addons.trigger("running")
        self.running = False

    def shutdown(self) -> None:
        # Idempotent shutdown.
        if getattr(self, "_shutdown", False):
            return
        self._shutdown = True
        self.addons.trigger("done")
        self.running = False