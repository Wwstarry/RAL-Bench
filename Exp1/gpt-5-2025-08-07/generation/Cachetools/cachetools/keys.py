from collections.abc import Mapping
from typing import Any, Iterable, Tuple


def deepfreeze(obj: Any) -> Any:
    """
    Convert nested mutable containers into hashable, recursively.

    - dict-like -> tuple of sorted (key, deepfreeze(value)) pairs
    - list/tuple -> tuple of deepfreeze(items)
    - set/frozenset -> frozenset of deepfreeze(items)
    - other objects -> unchanged if hashable; else fallback to repr(obj)
    """
    # Handle mappings
    if isinstance(obj, Mapping):
        # sort by key to ensure deterministic
        return tuple(sorted((k, deepfreeze(v)) for k, v in obj.items()))
    # Sequences (excluding strings/bytes)
    if isinstance(obj, (list, tuple)):
        return tuple(deepfreeze(x) for x in obj)
    # Sets
    if isinstance(obj, (set, frozenset)):
        return frozenset(deepfreeze(x) for x in obj)
    # Bytes/str are already hashable
    try:
        hash(obj)
    except TypeError:
        # Fallback: represent object
        return repr(obj)
    else:
        return obj


def _kwargs_items(kwargs: dict) -> Tuple[Tuple[Any, Any], ...]:
    if not kwargs:
        return ()
    return tuple(sorted((k, deepfreeze(v)) for k, v in kwargs.items()))


def hashkey(*args, **kwargs):
    """
    Build a hashable cache key from function arguments.

    This aims to be deterministic and robust against unhashable types by
    converting them via deepfreeze(). Keyword arguments are sorted.
    """
    frozen_args = deepfreeze(args)
    if kwargs:
        frozen_kwargs = _kwargs_items(kwargs)
        return (frozen_args, frozen_kwargs)
    else:
        return (frozen_args,)


def typedkey(*args, **kwargs):
    """
    Like hashkey, but includes argument types to distinguish e.g. 1 vs 1.0 vs True.
    """
    fk = hashkey(*args, **kwargs)
    # Collect types: positional types, keyword value types (sorted to mirror order)
    arg_types = tuple(type(a) for a in args)
    kw_types = tuple((k, type(v)) for k, v in sorted(kwargs.items()))
    return (fk, arg_types, kw_types)


def methodkey(self, *args, **kwargs):
    """
    Key function suitable for cachedmethod: include the bound instance in the key.
    """
    return hashkey(self, *args, **kwargs)