This is a minimal, safe-to-evaluate subset of mitmproxy.

It provides a small compatible API surface for tests:
- mitmproxy.http (HTTPFlow, Request, Response)
- mitmproxy.flow (Flow)
- mitmproxy.addonmanager (AddonManager)
- mitmproxy.tools.main.mitmdump (CLI entrypoint)
- mitmproxy.tools.dump.DumpMaster
- mitmproxy.tools.cmdline.mitmdump (argument parser)

No real traffic interception or MITM functionality is implemented.