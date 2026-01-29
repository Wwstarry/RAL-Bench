from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Error:
    """
    Minimal error container.
    """
    msg: str = ""


@dataclass
class Flow:
    """
    Base flow abstraction.

    In real mitmproxy, this is the basis for HTTPFlow, TCPFlow, DNSFlow, ...
    Here we keep it minimal but stable enough for import and basic interaction.
    """
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: float = field(default_factory=time.time)
    error: Optional[Error] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    intercepted: bool = False
    live: bool = False
    marked: str = ""

    def kill(self) -> None:
        """
        Mark flow as killed. Here we just set an error message.
        """
        self.error = self.error or Error("killed")

    def copy(self) -> "Flow":
        """
        Shallow copy that keeps metadata separate.
        """
        f = Flow()
        f.id = self.id
        f.created_at = self.created_at
        f.error = self.error
        f.metadata = dict(self.metadata)
        f.intercepted = self.intercepted
        f.live = self.live
        f.marked = self.marked
        return f