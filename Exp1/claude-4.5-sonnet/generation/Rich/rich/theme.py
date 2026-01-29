"""Theme support for Rich."""

from typing import Dict, Optional, Any


class Theme:
    """A container for style information."""

    def __init__(
        self,
        styles: Optional[Dict[str, Any]] = None,
        inherit: bool = True,
    ) -> None:
        self.styles = styles or {}
        self.inherit = inherit

    def __repr__(self) -> str:
        return f"Theme(styles={self.styles!r})"