from pygments.styles.default import DefaultStyle
from pygments.util import ClassNotFound

_STYLE_REGISTRY = {
    'default': DefaultStyle,
}

def get_style_by_name(name):
    if name in _STYLE_REGISTRY:
        return _STYLE_REGISTRY[name]
    raise ClassNotFound("Could not find style %r" % name)