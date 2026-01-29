"""Theme support for styling."""

from typing import Optional, Dict, Any


class Theme:
    """A theme for styling console output."""

    def __init__(self, styles: Optional[Dict[str, str]] = None):
        """Initialize a Theme."""
        self.styles = styles or {}

    def __getitem__(self, name: str) -> str:
        """Get a style by name."""
        return self.styles.get(name, "")

    def __setitem__(self, name: str, style: str) -> None:
        """Set a style by name."""
        self.styles[name] = style

    def get(self, name: str, default: str = "") -> str:
        """Get a style with a default."""
        return self.styles.get(name, default)