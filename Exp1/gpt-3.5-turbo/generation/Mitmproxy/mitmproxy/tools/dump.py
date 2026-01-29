from mitmproxy.flow import Flow


class DumpMaster:
    def __init__(self, options=None):
        self.options = options or {}
        self.running = False
        self.flows = []

    def run(self):
        self.running = True
        # Minimal run loop placeholder
        while self.running:
            # In real mitmproxy, this would handle flows and events.
            break

    def add_flow(self, flow: Flow):
        self.flows.append(flow)

    def shutdown(self):
        self.running = False