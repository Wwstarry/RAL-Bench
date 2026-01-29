import operator

import pytest

from cachetools import Cache, LRUCache, TTLCache, cached, cachedmethod
from cachetools.keys import hashkey, typedkey


def test_cache_base_mapping_semantics_and_maxsize_zero():
    c = Cache(maxsize=0)
    c["a"] = 1
    assert len(c) == 0
    assert c.currsize == 0
    assert c.get("a") is None

    # setdefault returns the value even if immediately evicted (dict-like)
    assert c.setdefault("x", 2) == 2
    assert "x" not in c


def test_cache_getsizeof_currsize_and_overwrite():
    c = LRUCache(maxsize=5, getsizeof=lambda v: v)
    c["a"] = 2
    c["b"] = 2
    assert c.currsize == 4
    c["a"] = 3
    assert c.currsize == 5
    # next insert forces eviction of LRU ('b' if 'a' accessed last by set)
    c["c"] = 1
    assert c.currsize <= 5
    assert len(c) == 2


def test_lru_access_updates_recency_and_get_updates_recency():
    c = LRUCache(maxsize=2)
    c["a"] = 1
    c["b"] = 2
    _ = c["a"]  # a becomes MRU, b LRU
    c["c"] = 3  # should evict b
    assert "a" in c and "c" in c and "b" not in c

    # get() should update recency similarly
    c = LRUCache(maxsize=2)
    c["a"] = 1
    c["b"] = 2
    assert c.get("a") == 1
    c["c"] = 3
    assert "b" not in c


def test_lru_iter_order_lru_to_mru():
    c = LRUCache(maxsize=3)
    c["a"] = 1
    c["b"] = 2
    c["c"] = 3
    _ = c["a"]  # order: b,c,a
    assert list(iter(c)) == ["b", "c", "a"]


class FakeTimer:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


def test_ttl_expiration_getitem_contains_len_iter():
    timer = FakeTimer()
    c = TTLCache(maxsize=10, ttl=5, timer=timer)
    c["a"] = 1
    assert c["a"] == 1
    assert "a" in c
    assert len(c) == 1
    assert list(c) == ["a"]

    timer.advance(5.01)
    assert "a" not in c
    assert c.get("a") is None
    with pytest.raises(KeyError):
        _ = c["a"]
    assert len(c) == 0
    assert list(c) == []


def test_ttl_lru_eviction_among_unexpired_and_purge_expired_first():
    timer = FakeTimer()
    c = TTLCache(maxsize=2, ttl=100, timer=timer)
    c["a"] = 1
    c["b"] = 2
    _ = c["a"]  # b is LRU
    c["c"] = 3
    assert "b" not in c and "a" in c and "c" in c

    # Purge expired first prevents eviction of fresh items
    timer = FakeTimer()
    c = TTLCache(maxsize=2, ttl=1, timer=timer)
    c["a"] = 1
    c["b"] = 2
    timer.advance(2)
    # both expired, inserting should not need to evict unexpired (none exist)
    c["c"] = 3
    assert list(c) == ["c"]
    assert "a" not in c and "b" not in c


def test_cached_decorator_basic_and_kwargs_order_insensitive():
    c = LRUCache(maxsize=100)
    calls = {"n": 0}

    @cached(c, key=hashkey)
    def f(a=0, b=0):
        calls["n"] += 1
        return a + b

    assert f(a=1, b=2) == 3
    assert f(b=2, a=1) == 3
    assert calls["n"] == 1


def test_typedkey_distinguishes_int_float():
    c = LRUCache(maxsize=100)
    calls = {"n": 0}

    @cached(c, key=typedkey)
    def ident(x):
        calls["n"] += 1
        return x

    assert ident(1) == 1
    assert ident(1.0) == 1.0
    assert calls["n"] == 2


def test_cachedmethod_per_instance_cache():
    class C:
        def __init__(self):
            self.cache = LRUCache(maxsize=100)
            self.calls = 0

        @cachedmethod(operator.attrgetter("cache"))
        def f(self, x):
            self.calls += 1
            return x * 2

    a = C()
    b = C()
    assert a.f(2) == 4
    assert a.f(2) == 4
    assert a.calls == 1

    assert b.f(2) == 4
    assert b.calls == 1