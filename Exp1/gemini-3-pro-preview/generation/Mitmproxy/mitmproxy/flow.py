import uuid
from mitmproxy import connections

class Flow:
    """
    Base class for flows.
    """
    def __init__(self, type: str, client_conn=None, server_conn=None, live=None):
        self.type = type
        self.id = str(uuid.uuid4())
        self.client_conn = client_conn or connections.ClientConnection()
        self.server_conn = server_conn or connections.ServerConnection()
        self.live = live
        self.error = None
        self.intercepted = False
        self.marked = False
        self.metadata = {}

    def resume(self):
        self.intercepted = False

    def kill(self):
        self.error = "Killed"
        self.intercepted = False

    def __repr__(self):
        return f"<Flow {self.id}>"

class Error:
    def __init__(self, msg: str):
        self.msg = msg
        self.timestamp = 0.0

    def __str__(self):
        return self.msg