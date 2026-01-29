"""
A **very** small stub of the real *mitmproxy* package.

The intention of this repository is **not** to ship a full-blown
man-in-the-middle proxy implementation – that would be far beyond the
scope and the security model of the execution environment in which this
code lives.

Instead we only expose the public symbols that are touched by the
benchmark / compatibility test-suite shipped with this repository.
Everything else is a no-op or a best-effort stub.

Only *import side-effects* (such as heavy native dependencies, network
initialisation, …) have been deliberately stripped to guarantee that the
module is always safe to import in a hermetic sandbox.
"""

from __future__ import annotations

__all__ = [
    "http",
    "flow",
    "addonmanager",
    "tools",
]

__version__: str = "0.0.0-stub"

# Re-export the key public modules so that code can do
# `from mitmproxy import http` or similar import tricks.
from importlib import import_module as _import_module  # noqa: E402

http = _import_module("mitmproxy.http")
flow = _import_module("mitmproxy.flow")
addonmanager = _import_module("mitmproxy.addonmanager")
tools = _import_module("mitmproxy.tools")