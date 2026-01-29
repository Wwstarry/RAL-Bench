from __future__ import annotations

from pygments.util import ClassNotFound

from .python import PythonLexer
from .json import JsonLexer
from .ini import IniLexer

_LEXERS = {}
for cls in (PythonLexer, JsonLexer, IniLexer):
    for a in getattr(cls, "aliases", []):
        _LEXERS[a.lower()] = cls
    # also index by class name
    _LEXERS[cls.__name__.lower()] = cls
    if getattr(cls, "name", ""):
        _LEXERS[cls.name.lower()] = cls


def get_lexer_by_name(_alias: str, **options):
    if not _alias:
        raise ClassNotFound(_alias)
    key = _alias.lower().strip()
    cls = _LEXERS.get(key)
    if cls is None:
        raise ClassNotFound(_alias)
    return cls(**options)


__all__ = ["PythonLexer", "JsonLexer", "IniLexer", "get_lexer_by_name"]