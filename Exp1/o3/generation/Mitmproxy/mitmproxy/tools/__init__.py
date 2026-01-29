"""
`mitmproxy.tools` is the namespace that bundles different front-end
executables in the real project (mitmdump, mitmproxy, mitmweb, …).

Only *mitmdump* is required for the compatibility test-suite, but we
still expose the package so users can do
```
from mitmproxy.tools import dump
```
without crashing.
"""
from importlib import import_module as _import_module

__all__ = ["dump", "main", "cmdline"]

# Lazily import sub-modules so that they are only loaded on demand.
dump = _import_module("mitmproxy.tools.dump")
main = _import_module("mitmproxy.tools.main")
cmdline = _import_module("mitmproxy.tools.cmdline")