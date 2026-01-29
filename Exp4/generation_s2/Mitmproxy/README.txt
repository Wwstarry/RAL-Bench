This is a minimal, safe-to-evaluate subset of the mitmproxy project.

It intentionally does not implement any real proxying, TLS interception, or man-in-the-middle features.
It only provides a small set of modules, classes, and CLI entrypoints for unit-test validation.

Included surfaces:
- mitmproxy.http (HTTPFlow, Request, Response)
- mitmproxy.flow (Flow)
- mitmproxy.addonmanager (AddonManager)
- mitmproxy.tools.main.mitmdump (CLI entry function mitmdump)
- mitmproxy.tools.dump (DumpMaster)
- mitmproxy.tools.cmdline.mitmdump (argument parsing helpers)