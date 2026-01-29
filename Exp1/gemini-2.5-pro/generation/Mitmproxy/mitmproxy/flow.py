import uuid
import time
from typing import Optional

class Flow:
    """
    A stub for the base Flow class.

    Flows are the central data structure in mitmproxy.
    """
    def __init__(self):
        self.id: str = str(uuid.uuid4())
        self.client_conn = None
        self.server_conn = None
        self.error: Optional[str] = None
        self.intercepted: bool = False
        self.live: bool = True
        self.timestamp_created: float = time.time()

    def __repr__(self):
        return f"<{type(self).__name__} {self.id}>"