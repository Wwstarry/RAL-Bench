"""Base cache implementation."""

from collections.abc import MutableMapping


class Cache(MutableMapping):
    """Base cache class implementing the MutableMapping interface."""

    def __init__(self, maxsize):
        """Initialize cache with maximum size.
        
        Args:
            maxsize: Maximum number of items to store in the cache.
        """
        self.__data = {}
        self.__maxsize = maxsize

    def __setitem__(self, key, value):
        """Set an item in the cache, evicting if necessary."""
        maxsize = self.__maxsize
        if maxsize is None or maxsize <= 0:
            raise ValueError('maxsize must be a positive integer or None')
        
        if key not in self.__data and len(self.__data) >= maxsize:
            self.popitem()
        
        self.__data[key] = value

    def __getitem__(self, key):
        """Get an item from the cache."""
        return self.__data[key]

    def __delitem__(self, key):
        """Delete an item from the cache."""
        del self.__data[key]

    def __contains__(self, key):
        """Check if a key is in the cache."""
        return key in self.__data

    def __iter__(self):
        """Iterate over cache keys."""
        return iter(self.__data)

    def __len__(self):
        """Return the number of items in the cache."""
        return len(self.__data)

    def __repr__(self):
        """Return string representation of the cache."""
        return f'{self.__class__.__name__}({dict(self.__data)!r}, maxsize={self.__maxsize})'

    def popitem(self):
        """Remove and return an arbitrary (key, value) pair from the cache."""
        key, value = self.__data.popitem()
        return key, value

    @property
    def maxsize(self):
        """Return the maximum size of the cache."""
        return self.__maxsize

    @property
    def currsize(self):
        """Return the current number of items in the cache."""
        return len(self.__data)