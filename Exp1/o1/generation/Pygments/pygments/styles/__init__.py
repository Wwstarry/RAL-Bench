"""
Style registry.
"""

from ..util import ClassNotFound
from .default import DefaultStyle

_styles_by_name = {
    'default': DefaultStyle,
}

def get_style_by_name(name):
    name = name.lower()
    if name in _styles_by_name:
        return _styles_by_name[name]()
    raise ClassNotFound("No style named %r found." % name)