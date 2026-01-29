from __future__ import annotations

from typing import Dict, Optional


class Theme:
    """
    Minimal Theme container to satisfy simple theme usage.
    This implementation does not apply styles; it just stores them.
    """

    def __init__(self, styles: Optional[Dict[str, str]] = None, inherit: bool = True) -> None:
        self.styles: Dict[str, str] = dict(styles or {})
        self.inherit = inherit

    def __getitem__(self, key: str) -> str:
        return self.styles[key]

    def __setitem__(self, key: str, value: str) -> None:
        self.styles[key] = value

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.styles.get(key, default)

    def update(self, other: Dict[str, str]) -> None:
        self.styles.update(other)