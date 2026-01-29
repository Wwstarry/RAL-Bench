"""
Utility functions for Click.
"""

from typing import Any, Callable, Optional


def make_str(value: Any) -> str:
    """Convert a value to a string."""
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def make_default_short_help(help_text: str, max_length: int = 45) -> str:
    """Create a short help text from a longer one."""
    if not help_text:
        return ""
    
    # Take first sentence or first line
    text = help_text.split("\n")[0]
    text = text.split(".")[0]
    
    if len(text) > max_length:
        text = text[:max_length].rsplit(" ", 1)[0] + "..."
    
    return text