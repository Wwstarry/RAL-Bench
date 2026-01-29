"""Key functions for caching."""


def hashkey(*args, **kwargs):
    """Create a cache key from function arguments."""
    return _HashedTuple(args + tuple(sorted(kwargs.items())))


def typedkey(*args, **kwargs):
    """Create a typed cache key from function arguments."""
    key = args
    if kwargs:
        key += (object(),) + tuple(sorted(kwargs.items()))
    # Include types in the key
    key += tuple(type(arg) for arg in args)
    if kwargs:
        key += tuple(type(v) for k, v in sorted(kwargs.items()))
    return _HashedTuple(key)


class _HashedTuple(tuple):
    """A tuple that caches its hash value."""
    
    __slots__ = ('_hash',)
    
    def __new__(cls, items):
        self = super().__new__(cls, items)
        return self
    
    def __hash__(self):
        if not hasattr(self, '_hash'):
            object.__setattr__(self, '_hash', tuple.__hash__(self))
        return self._hash
    
    def __eq__(self, other):
        return tuple.__eq__(self, other)
    
    def __ne__(self, other):
        return tuple.__ne__(self, other)