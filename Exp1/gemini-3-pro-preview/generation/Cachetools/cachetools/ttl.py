import time
from .lru import LRUCache
from collections import OrderedDict

class TTLCache(LRUCache):
    """LRU Cache implementation with per-item time-to-live (TTL) value."""

    def __init__(self, maxsize, ttl, timer=time.monotonic, getsizeof=None):
        LRUCache.__init__(self, maxsize, getsizeof)
        self.__ttl = ttl
        self.__timer = timer
        # Map key -> expiration_time. 
        # Since TTL is constant, insertion order is expiration order.
        self.__expires = OrderedDict()

    def __repr__(self):
        return '%s(%r, maxsize=%r, currsize=%r)' % (
            self.__class__.__name__,
            list(self.items()),
            self.maxsize,
            self.currsize,
        )

    def __getitem__(self, key, lru_getitem=LRUCache.__getitem__):
        try:
            value = lru_getitem(self, key)
        except KeyError:
            return self.__missing__(key)
            
        if key in self.__expires:
            if self.__timer() > self.__expires[key]:
                del self[key]
                return self.__missing__(key)
        return value

    def __setitem__(self, key, value, lru_setitem=LRUCache.__setitem__):
        lru_setitem(self, key, value)
        # Update expiration
        self.__expires[key] = self.__timer() + self.__ttl
        # Move to end to maintain expiration order (since TTL is constant)
        self.__expires.move_to_end(key)
        self.expire()

    def __delitem__(self, key, lru_delitem=LRUCache.__delitem__):
        lru_delitem(self, key)
        if key in self.__expires:
            del self.__expires[key]

    def __iter__(self):
        # Iterate over all items, but we must check expiry to be consistent
        # with the requirement that expired items are treated as missing.
        # However, standard iteration usually just iterates keys.
        # To strictly match reference behavior which might lazily expire:
        # We iterate over the underlying structure.
        # Note: Modifying dict during iteration is bad, so we don't expire here.
        # We just yield keys.
        return super().__iter__()

    def __len__(self):
        return super().__len__()

    @property
    def ttl(self):
        """The time-to-live value of the cache's items."""
        return self.__ttl

    @property
    def timer(self):
        """The timer function used by the cache."""
        return self.__timer

    def expire(self, time=None):
        """Remove expired items from the cache."""
        if time is None:
            time = self.__timer()
        
        # Since __expires is ordered by insertion (and thus by expiration time),
        # we can just pop from the start until we find a non-expired item.
        while self.__expires:
            key, expires = next(iter(self.__expires.items()))
            if time > expires:
                del self[key]
            else:
                break