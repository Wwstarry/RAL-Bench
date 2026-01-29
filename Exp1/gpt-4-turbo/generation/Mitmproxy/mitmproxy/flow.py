# Minimal mitmproxy.flow API surface

from typing import Any


class Flow:
    def __init__(self):
        self.metadata = {}

    def __repr__(self):
        return f"<Flow metadata={self.metadata}>"