"""
Styles for Pygments.
"""

from pygments.util import ClassNotFound


def get_style_by_name(name):
    """Get a style by its name."""
    name_lower = name.lower()
    
    if name_lower in ('default',):
        from pygments.styles.default import DefaultStyle
        return DefaultStyle
    else:
        raise ClassNotFound(f"No style found for name {name!r}")


__all__ = ['get_style_by_name']