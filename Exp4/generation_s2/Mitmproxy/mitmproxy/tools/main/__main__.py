from __future__ import annotations

import sys

from mitmproxy.tools.main.mitmdump import main as mitmdump_main

if __name__ == "__main__":
    # Default to mitmdump behavior for "python -m mitmproxy.tools.main"
    mitmdump_main()