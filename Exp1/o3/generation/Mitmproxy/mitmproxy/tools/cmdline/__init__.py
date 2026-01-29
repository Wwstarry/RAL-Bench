"""
mitmproxy.tools.cmdline – argument parser construction helpers.

The public test-suite uses `mitmproxy.tools.cmdline.mitmdump` to obtain
an *ArgumentParser* for help/usage text verification.
"""
from importlib import import_module as _import_module

mitmdump = _import_module("mitmproxy.tools.cmdline.mitmdump")