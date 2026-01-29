"""
Implementation skeleton of the *mitmdump* head-less front-end.

In the real project DumpMaster inherits a fully-featured `Master`
implementation that manages the event-loop, networking, addons, io, …

For the stub we only expose a callable `DumpMaster.run()` method so that
tests can spin it up without side-effects.  **No real traffic is ever
intercepted or generated.**
"""
from __future__ import annotations

import contextlib
import time
from typing import Any, Dict, List, Sequence

from ..addonmanager import AddonManager


class DumpMaster(AddonManager):
    """
    Extremely simplified variant of mitmproxy.tools.dump.DumpMaster
    suitable for CLI smoke-tests.
    """

    def __init__(
        self,
        options: Dict[str, Any] | None = None,
        addons: Sequence[Any] | None = None,
        with_termlog: bool = False,
        with_dumper: bool = False,
    ) -> None:
        super().__init__(options)
        # In real mitmproxy *termlog* / *dumper* are addons.  We silently
        # ignore the flags.  They are only here because the real
        # signature exposes them.
        self.with_termlog = with_termlog
        self.with_dumper = with_dumper

        # Pre-register user supplied addons so that tests can verify that
        # `DumpMaster.addons` gets populated.
        for addon in addons or []:
            self.register(addon)

        self._running: bool = False

    # ------------------------------------------------------------------
    # Life-cycle helpers
    # ------------------------------------------------------------------
    def run(self) -> int:
        """
        Block until :py:meth:`shutdown` is called.

        The stub just sleeps a tiny bit to emulate long-running IO and
        then exits immediately.  The return code mimics the typical
        convention where *0* means success.
        """
        self._running = True
        # Simulate a tiny bit of work so that a poorly written test that
        # expects some time to pass does not trip.
        with contextlib.suppress(TimeoutError):
            time.sleep(0.01)
        return 0

    def shutdown(self) -> None:
        """Stop the master loop (no-op in the stub)."""
        self._running = False

    # ------------------------------------------------------------------
    # Representation helpers
    # ------------------------------------------------------------------
    def __repr__(self) -> str:  # noqa: D401
        state = "running" if self._running else "stopped"
        return f"<DumpMaster {state}, {len(self.addons)} addons>"