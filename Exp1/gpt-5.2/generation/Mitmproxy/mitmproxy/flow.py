from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Flow:
    """
    Base flow abstraction.

    This is a minimal stand-in for mitmproxy.flow.Flow. It stores metadata,
    an id, and a simple error attribute.
    """
    id: str = ""
    type: str = "flow"
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[BaseException] = None

    def set_error(self, exc: BaseException) -> None:
        self.error = exc

    def copy(self) -> "Flow":
        # simple shallow-ish copy suitable for tests
        f = type(self)(id=self.id, type=self.type)
        f.metadata = dict(self.metadata)
        f.error = self.error
        return f