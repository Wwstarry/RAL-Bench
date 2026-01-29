from ..util import ClassNotFound
from .default import DefaultStyle

_style_by_name = {
    "default": DefaultStyle,
}

def get_style_by_name(name):
    cls = _style_by_name.get(name.lower())
    if not cls:
        raise ClassNotFound(f"No style for name '{name}'")
    return cls