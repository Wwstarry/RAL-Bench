"""
Minimal Options object for mitmproxy tools.

This module provides a simple attribute bag with light conveniences to set
options from --set key=value strings typical in mitmproxy CLIs.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional


class Options:
    """
    Simple options container with attribute access.
    """

    def __init__(self, **kwargs: Any) -> None:
        # Defaults similar to mitmdump typical values, but safe and inert.
        self.listen_host: str = "127.0.0.1"
        self.listen_port: int = 8080
        self.scripts: list[str] = []
        self.mode: str = "regular"
        self.verbosity: int = 0
        self.quiet: int = 0
        # Allow arbitrary extension
        for k, v in kwargs.items():
            setattr(self, k, v)

    def update(self, mapping: Dict[str, Any]) -> None:
        for k, v in mapping.items():
            setattr(self, k, v)

    def set(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def update_from_set_strings(self, items: Optional[Iterable[str]]) -> None:
        if not items:
            return
        updates: Dict[str, Any] = {}
        for item in items:
            if "=" not in item:
                # anything without '=' is treated as a boolean true switch
                updates[item] = True
                continue
            k, v = item.split("=", 1)
            updates[k.strip()] = self._coerce_value(v.strip())
        self.update(updates)

    @staticmethod
    def _coerce_value(v: str) -> Any:
        lower = v.lower()
        # try bool
        if lower in ("true", "yes", "on"):
            return True
        if lower in ("false", "no", "off"):
            return False
        # try int
        try:
            return int(v)
        except ValueError:
            pass
        # try float
        try:
            return float(v)
        except ValueError:
            pass
        # otherwise string
        return v

    def __repr__(self) -> str:
        # Show a minimal helpful representation
        return f"Options(listen_host={self.listen_host!r}, listen_port={self.listen_port!r}, mode={self.mode!r})"