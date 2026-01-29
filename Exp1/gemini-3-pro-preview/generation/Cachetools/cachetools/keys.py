class _HashedTuple(tuple):
    """A tuple subclass that caches its hash value."""
    __hash_value = None

    def __hash__(self, hash=hash):
        if self.__hash_value is None:
            self.__hash_value = hash(super().__hash__())
        return self.__hash_value

    def __add__(self, other, add=tuple.__add__):
        return _HashedTuple(add(self, other))

    def __radd__(self, other, add=tuple.__add__):
        return _HashedTuple(add(other, self))

    def __getstate__(self):
        return {}

def hashkey(*args, **kwargs):
    """Return a cache key for the specified hashable arguments."""
    if kwargs:
        return _HashedTuple(args + sum(sorted(kwargs.items()), ()))
    return _HashedTuple(args)

def typedkey(*args, **kwargs):
    """Return a cache key for the specified hashable arguments, including types."""
    key = hashkey(*args, **kwargs)
    key += tuple(type(v) for v in args)
    key += tuple(type(v) for _, v in sorted(kwargs.items()))
    return key