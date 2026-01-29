"""Flow base abstractions"""

from typing import Optional, Dict, Any

class Flow:
    def __init__(self):
        self.id: str = ""
        self.intercepted: bool = False
        self.modified: bool = False
        self.marked: bool = False
        self.comment: str = ""
        self.error: Optional[dict] = None
        self.type: str = "base"
        self.timestamp_created: float = 0.0
        self.timestamp_start: float = 0.0
        self.timestamp_end: float = 0.0