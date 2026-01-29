from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Tuple


@dataclass
class Options:
    """
    Minimal options container.

    This is *not* the real mitmproxy options system. It only stores a few common
    fields and supports applying --set key=value pairs.
    """

    listen_port: int = 8080
    quiet: bool = False
    verbose: bool = False
    script: str | None = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def update(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

    def apply_set(self, items: Iterable[str]) -> List[Tuple[str, str]]:
        """
        Apply a sequence of "key=value" strings into self.extra.
        Returns a list of (key, value) pairs that were set.
        """
        applied: List[Tuple[str, str]] = []
        for item in items:
            if not isinstance(item, str):
                continue
            if "=" in item:
                k, v = item.split("=", 1)
            else:
                k, v = item, ""
            k = k.strip()
            # Keep value as-is (except strip only outer whitespace) for determinism.
            v = v.strip()
            if k:
                self.extra[k] = v
                applied.append((k, v))
        return applied