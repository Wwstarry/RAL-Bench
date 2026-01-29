# Base cache class

class Cache(dict):
    """Base class for cache implementations."""

    def __init__(self, maxsize):
        if maxsize <= 0:
            raise ValueError("maxsize must be greater than 0")
        self.maxsize = maxsize
        super().__init__()

    def __setitem__(self, key, value):
        if len(self) >= self.maxsize:
            self.evict()
        super().__setitem__(key, value)

    def evict(self):
        """Evict an item from the cache."""
        raise NotImplementedError("Subclasses must implement evict()")