from __future__ import annotations

from typing import Optional

from mitmproxy import ctx
from mitmproxy.addonmanager import AddonManager
from mitmproxy.command import CommandManager
from mitmproxy.flow import Flow
from mitmproxy.options import Options


class DumpMaster:
    """
    Safe-to-evaluate dummy master class for mitmdump.
    """

    def __init__(
        self,
        options: Optional[Options] = None,
        with_termlog: bool = True,
        with_dumper: bool = True,
    ):
        self.options: Options = options if options is not None else Options()
        self.should_exit: bool = False
        self.last_exception = None

        self.commands = CommandManager(self)
        self.addons = AddonManager(self)

        # populate global context for addons that import ctx
        ctx.ctx.master = self
        ctx.ctx.options = self.options

        self.with_termlog = bool(with_termlog)
        self.with_dumper = bool(with_dumper)

    def run(self) -> None:
        # No loop, just lifecycle hooks.
        self.addons.trigger("running")
        if not self.should_exit:
            self.addons.trigger("done")

    def shutdown(self) -> None:
        self.should_exit = True

    def load_flow(self, flow: Flow) -> None:
        # Optional hook in real mitmproxy.
        self.addons.trigger("load", flow)