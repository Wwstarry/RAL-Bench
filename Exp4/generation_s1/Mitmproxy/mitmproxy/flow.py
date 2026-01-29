from __future__ import annotations

import copy
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Error:
    msg: str = ""
    timestamp: float = 0.0

    def __init__(self, msg: str = "", timestamp: Optional[float] = None):
        self.msg = msg
        self.timestamp = time.time() if timestamp is None else float(timestamp)

    def __str__(self) -> str:
        return self.msg

    def __repr__(self) -> str:
        return f"Error(msg={self.msg!r}, timestamp={self.timestamp!r})"


class Flow:
    """
    Minimal Flow base class.

    This provides metadata and basic lifecycle flags. No networking side effects.
    """

    def __init__(self) -> None:
        self.id: str = uuid.uuid4().hex
        self.error: Optional[Error] = None
        self.intercepted: bool = False
        self.marked: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
        self.live: bool = False

    def kill(self) -> None:
        # In real mitmproxy, kill aborts connections. Here we only mark an error.
        if self.error is None:
            self.error = Error("killed")

    def copy(self) -> "Flow":
        f = copy.copy(self)
        f.metadata = copy.deepcopy(self.metadata)
        return f

    def get_state(self) -> Dict[str, Any]:
        return {
            "type": self.__class__.__name__,
            "id": self.id,
            "error": None if self.error is None else {"msg": self.error.msg, "timestamp": self.error.timestamp},
            "intercepted": self.intercepted,
            "marked": self.marked,
            "metadata": copy.deepcopy(self.metadata),
            "live": self.live,
        }

    def set_state(self, state: Dict[str, Any]) -> None:
        self.id = state.get("id", self.id)
        err = state.get("error", None)
        if err is None:
            self.error = None
        else:
            self.error = Error(err.get("msg", ""), err.get("timestamp", None))
        self.intercepted = bool(state.get("intercepted", False))
        self.marked = state.get("marked", None)
        self.metadata = copy.deepcopy(state.get("metadata", {}))
        self.live = bool(state.get("live", False))


class FlowReader:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError("FlowReader is not implemented in this minimal subset.")


class FlowWriter:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError("FlowWriter is not implemented in this minimal subset.")