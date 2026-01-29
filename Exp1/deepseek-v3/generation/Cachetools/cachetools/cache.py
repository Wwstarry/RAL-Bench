import time
from collections import OrderedDict
from threading import RLock


class Cache(dict):
    """Base cache class with dictionary-like interface."""
    
    def __init__(self, maxsize, getsizeof=None):
        if maxsize is not None and maxsize <= 0:
            raise ValueError("maxsize must be positive")
        
        super().__init__()
        self.maxsize = maxsize
        self.getsizeof = getsizeof
        self._lock = RLock()
    
    def __getitem__(self, key):
        with self._lock:
            return super().__getitem__(key)
    
    def __setitem__(self, key, value):
        with self._lock:
            size = self.getsizeof(value) if self.getsizeof else 1
            if self.maxsize is not None and size > self.maxsize:
                raise ValueError("value too large")
            
            super().__setitem__(key, value)
            self._cache_setitem(key, value, size)
    
    def __delitem__(self, key):
        with self._lock:
            super().__delitem__(key)
            self._cache_delitem(key)
    
    def __missing__(self, key):
        raise KeyError(key)
    
    def __contains__(self, key):
        with self._lock:
            return super().__contains__(key)
    
    def get(self, key, default=None):
        with self._lock:
            try:
                return self[key]
            except KeyError:
                return default
    
    def pop(self, key, default=None):
        with self._lock:
            try:
                value = self[key]
                del self[key]
                return value
            except KeyError:
                return default
    
    def setdefault(self, key, default=None):
        with self._lock:
            try:
                return self[key]
            except KeyError:
                self[key] = default
                return default
    
    def clear(self):
        with self._lock:
            super().clear()
            self._cache_clear()
    
    def _cache_setitem(self, key, value, size):
        pass
    
    def _cache_delitem(self, key):
        pass
    
    def _cache_clear(self):
        pass


class LRUCache(Cache):
    """Least Recently Used (LRU) cache implementation."""
    
    def __init__(self, maxsize, getsizeof=None):
        super().__init__(maxsize, getsizeof)
        self.__order = OrderedDict()
        self._size = 0
    
    def __getitem__(self, key):
        with self._lock:
            value = super().__getitem__(key)
            # Move to end (most recently used)
            self.__order.move_to_end(key)
            return value
    
    def __setitem__(self, key, value):
        with self._lock:
            if key in self:
                # Update existing item
                old_value = self[key]
                old_size = self.getsizeof(old_value) if self.getsizeof else 1
                new_size = self.getsizeof(value) if self.getsizeof else 1
                
                if new_size > old_size and self.maxsize is not None:
                    if self._size - old_size + new_size > self.maxsize:
                        self._evict(new_size - old_size)
                
                super().__setitem__(key, value)
                self.__order.move_to_end(key)
                self._size = self._size - old_size + new_size
            else:
                # Add new item
                size = self.getsizeof(value) if self.getsizeof else 1
                if self.maxsize is not None:
                    if size > self.maxsize:
                        raise ValueError("value too large")
                    if self._size + size > self.maxsize:
                        self._evict(size)
                
                super().__setitem__(key, value)
                self.__order[key] = None
                self._size += size
    
    def __delitem__(self, key):
        with self._lock:
            value = self[key]
            size = self.getsizeof(value) if self.getsizeof else 1
            super().__delitem__(key)
            del self.__order[key]
            self._size -= size
    
    def _cache_setitem(self, key, value, size):
        pass  # Handled in __setitem__
    
    def _cache_delitem(self, key):
        pass  # Handled in __delitem__
    
    def _cache_clear(self):
        self.__order.clear()
        self._size = 0
    
    def _evict(self, extra_size=0):
        """Evict least recently used items until there's enough space."""
        while self.__order and self.maxsize is not None and self._size + extra_size > self.maxsize:
            key, _ = self.__order.popitem(last=False)
            value = super().__getitem__(key)
            size = self.getsizeof(value) if self.getsizeof else 1
            super().__delitem__(key)
            self._size -= size


class TTLCache(Cache):
    """Time To Live (TTL) cache implementation."""
    
    def __init__(self, maxsize, ttl, timer=time.time, getsizeof=None):
        super().__init__(maxsize, getsizeof)
        self.__ttl = ttl
        self.__timer = timer
        self.__times = {}
        self._size = 0
    
    def __contains__(self, key):
        with self._lock:
            if key not in self.__times:
                return False
            if self.__timer() > self.__times[key]:
                del self[key]
                return False
            return True
    
    def __getitem__(self, key):
        with self._lock:
            if key not in self.__times:
                raise KeyError(key)
            
            timestamp = self.__times[key]
            if self.__timer() > timestamp:
                del self[key]
                raise KeyError(key)
            
            return super().__getitem__(key)
    
    def __setitem__(self, key, value):
        with self._lock:
            size = self.getsizeof(value) if self.getsizeof else 1
            if self.maxsize is not None and size > self.maxsize:
                raise ValueError("value too large")
            
            # Remove expired items first
            self._expire()
            
            if key in self:
                # Update existing item
                old_value = super().__getitem__(key)
                old_size = self.getsizeof(old_value) if self.getsizeof else 1
                
                if self.maxsize is not None:
                    if size > old_size and self._size - old_size + size > self.maxsize:
                        self._evict(size - old_size)
                
                super().__setitem__(key, value)
                self.__times[key] = self.__timer() + self.__ttl
                self._size = self._size - old_size + size
            else:
                # Add new item
                if self.maxsize is not None:
                    if self._size + size > self.maxsize:
                        self._evict(size)
                
                super().__setitem__(key, value)
                self.__times[key] = self.__timer() + self.__ttl
                self._size += size
    
    def __delitem__(self, key):
        with self._lock:
            value = super().__getitem__(key)
            size = self.getsizeof(value) if self.getsizeof else 1
            super().__delitem__(key)
            del self.__times[key]
            self._size -= size
    
    def _cache_setitem(self, key, value, size):
        pass  # Handled in __setitem__
    
    def _cache_delitem(self, key):
        pass  # Handled in __delitem__
    
    def _cache_clear(self):
        self.__times.clear()
        self._size = 0
    
    def _expire(self):
        """Remove expired items."""
        now = self.__timer()
        expired = [key for key, timestamp in self.__times.items() if now > timestamp]
        for key in expired:
            try:
                del self[key]
            except KeyError:
                pass
    
    def _evict(self, extra_size=0):
        """Evict items until there's enough space."""
        self._expire()  # Remove expired items first
        
        # If still not enough space, remove by insertion order
        while self.__times and self.maxsize is not None and self._size + extra_size > self.maxsize:
            # Get the oldest item
            key = next(iter(self.__times))
            value = super().__getitem__(key)
            size = self.getsizeof(value) if self.getsizeof else 1
            super().__delitem__(key)
            del self.__times[key]
            self._size -= size