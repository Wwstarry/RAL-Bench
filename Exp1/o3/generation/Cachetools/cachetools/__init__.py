"""
Minimal yet mostly API–compatible re-implementation of the public interface of
the excellent ‘cachetools’ project.

Only the core functionality required by the test-suite is provided:
    * Cache, LRUCache, TTLCache base classes
    * Decorators: cached, cachedmethod
    * Key helpers located in cachetools.keys
    * Module level namespaces:  cachetools.cache, cachetools.lru, cachetools.ttl
"""
from types import ModuleType
import sys

# --------------------------------------------------------------------------- #
# Public sub-modules (real python files – see ./cache.py, ./decorators.py …)  #
# --------------------------------------------------------------------------- #
from .cache import Cache, LRUCache, TTLCache               # noqa: E402
from .decorators import cached, cachedmethod               # noqa: E402
from . import keys as keys                                 # noqa: E402

__all__ = [
    # cache objects
    "Cache",
    "LRUCache",
    "TTLCache",
    # decorators
    "cached",
    "cachedmethod",
    # helpers
    "keys",
]

# --------------------------------------------------------------------------- #
# Provide additional namespaces so `import cachetools.lru as lru` is valid.   #
# They dynamically proxy back to the single source of truth inside            #
# cachetools.cache to avoid code duplication.                                 #
# --------------------------------------------------------------------------- #
def _create_proxy(name, public_objects):
    mod = ModuleType(f"{__name__}.{name}")
    globals_ = globals()
    for attr in public_objects:
        mod.__dict__[attr] = globals_[attr]
    sys.modules[mod.__name__] = mod


_create_proxy("cache", ["Cache"])
_create_proxy("lru", ["LRUCache"])
_create_proxy("ttl", ["TTLCache"])