from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Error:
    msg: str = ""
    timestamp: Optional[float] = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = time.time()

    def get_state(self) -> Dict[str, Any]:
        return {"msg": self.msg, "timestamp": self.timestamp}

    @classmethod
    def from_state(cls, state: Dict[str, Any]) -> "Error":
        return cls(msg=state.get("msg", ""), timestamp=state.get("timestamp"))


class Flow:
    """
    Minimal base Flow abstraction.

    This does not implement mitmproxy's full lifecycle; it only provides fields,
    representation, and (de)serialization used in tests.
    """

    id: str
    type: str
    error: Optional[Exception]
    intercepted: bool
    live: bool
    metadata: Dict[str, Any]

    def __init__(self, id: Optional[str] = None, type: str = "flow"):
        self.id = id or str(uuid.uuid4())
        self.type = type
        self.error = None
        self.intercepted = False
        self.live = False
        self.metadata = {}

    def __repr__(self) -> str:
        return f"<Flow id={self.id!r} type={self.type!r}>"

    def get_state(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "intercepted": bool(self.intercepted),
            "live": bool(self.live),
            "metadata": dict(self.metadata) if isinstance(self.metadata, dict) else {},
        }

    def set_state(self, state: Dict[str, Any]) -> None:
        if not isinstance(state, dict):
            return
        if "id" in state and isinstance(state["id"], str):
            self.id = state["id"]
        if "type" in state and isinstance(state["type"], str):
            self.type = state["type"]
        if "intercepted" in state:
            self.intercepted = bool(state.get("intercepted"))
        if "live" in state:
            self.live = bool(state.get("live"))
        if "metadata" in state and isinstance(state["metadata"], dict):
            self.metadata = dict(state["metadata"])