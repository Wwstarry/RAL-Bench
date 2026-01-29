# Minimal mitmproxy.tools.dump API surface

class DumpMaster:
    def __init__(self, options=None):
        self.options = options or {}

    def run(self):
        print("DumpMaster running with options:", self.options)