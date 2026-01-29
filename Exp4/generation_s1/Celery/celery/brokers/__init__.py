from __future__ import annotations

from typing import Callable, Optional

from .memory import MemoryBroker


def get_broker_by_url(url: str, dispatch: Optional[Callable[[dict], None]] = None):
    if not url or url.startswith("memory://"):
        return MemoryBroker(dispatch=dispatch)
    # Fallback to memory for unknown schemes in this minimal implementation
    return MemoryBroker(dispatch=dispatch)