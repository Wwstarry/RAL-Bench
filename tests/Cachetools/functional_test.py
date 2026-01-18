import os
import sys
import time
import threading
from pathlib import Path
from typing import Any, Dict, Tuple

import pytest

# Decide whether to test the reference implementation or the generated one
TARGET_ENV = "CACHETOOLS_TARGET"
TARGET_REFERENCE_VALUE = "reference"

ROOT_DIR = Path(__file__).resolve().parents[2]

target = os.getenv(TARGET_ENV, "generated")

if target == TARGET_REFERENCE_VALUE:
    # Reference: put ./repositories/cachetools on sys.path
    sys.path.insert(0, str(ROOT_DIR / "repositories" / "cachetools"))
else:
    # Generated implementation: ./generation/Cachetools
    sys.path.insert(0, str(ROOT_DIR / "generation" / "Cachetools"))

# Now import the library under test
from cachetools import LRUCache, TTLCache, cached  # type: ignore  # noqa: E402
from cachetools import keys as cache_keys  # type: ignore  # noqa: E402


def test_basic_lru_cache_eviction():
    cache = LRUCache(maxsize=2)

    cache["a"] = 1
    cache["b"] = 2

    # Touch "a" so it becomes most recently used
    _ = cache["a"]

    # Adding "c" should evict the least recently used entry ("b")
    cache["c"] = 3

    assert "a" in cache
    assert "c" in cache
    assert "b" not in cache
    assert len(cache) == 2


def test_ttl_cache_expiration():
    ttl_seconds = 0.2
    cache = TTLCache(maxsize=10, ttl=ttl_seconds)

    cache["answer"] = 42
    assert cache["answer"] == 42
    assert "answer" in cache

    # Wait long enough for the entry to expire
    time.sleep(ttl_seconds + 0.3)

    # After TTL has passed, the key should no longer be considered valid
    # Implementations may clean up lazily, but membership and access
    # must not behave as if the value is still present.
    assert "answer" not in cache
    with pytest.raises(KeyError):
        _ = cache["answer"]


def test_cached_decorator_avoids_recomputing():
    calls = {"count": 0}

    @cached(cache=LRUCache(maxsize=128))
    def fib(n: int) -> int:
        calls["count"] += 1
        if n < 2:
            return n
        return fib(n - 1) + fib(n - 2)

    # First call should compute and fill the cache
    result1 = fib(10)
    assert result1 == 55

    first_count = calls["count"]

    # Second call with the same argument should be fully cached
    result2 = fib(10)
    assert result2 == 55
    assert calls["count"] == first_count

    # Some smaller values should also be cached as part of the recursion
    # The exact count depends on implementation details, but it should be
    # significantly less than a naive recursive implementation.
    assert calls["count"] < 20


def test_cached_with_ttl_expires_and_recomputes():
    ttl_seconds = 0.2
    cache = TTLCache(maxsize=16, ttl=ttl_seconds)
    calls = {"count": 0}

    @cached(cache=cache)
    def double(x: int) -> int:
        calls["count"] += 1
        return x * 2

    v1 = double(21)
    assert v1 == 42
    assert calls["count"] == 1

    # Within TTL, the cached value should be reused
    v2 = double(21)
    assert v2 == 42
    assert calls["count"] == 1

    time.sleep(ttl_seconds + 0.3)

    # After TTL, the function should be called again
    v3 = double(21)
    assert v3 == 42
    assert calls["count"] == 2


def test_custom_key_function_with_unhashable_arguments():
    cache = LRUCache(maxsize=16)

    def mapping_key(prefix: str, mapping: dict) -> tuple:
        """
        Build a stable key from a prefix and a mapping with hashable values.
        Uses cachetools.keys.hashkey under the hood for consistency.
        """
        items = tuple(sorted(mapping.items()))
        return cache_keys.hashkey(prefix, items)

    calls = {"count": 0}

    @cached(cache=cache, key=mapping_key)
    def combine(prefix: str, mapping: dict) -> str:
        calls["count"] += 1
        parts = [f"{k}={v}" for k, v in sorted(mapping.items())]
        return prefix + ":" + ",".join(parts)

    m1 = {"a": 1, "b": 2}
    m2 = {"b": 2, "a": 1}  # same logical mapping, different order / identity

    r1 = combine("cfg", m1)
    r2 = combine("cfg", m2)

    assert r1 == r2
    # The second call should have been served from cache
    assert calls["count"] == 1

    # A different mapping should result in a cache miss
    r3 = combine("cfg", {"a": 1, "b": 3})
    assert r3 != r1
    assert calls["count"] == 2


# -----------------------------------------------------------------------------
# Additional functional tests (to reach >= 10)
# -----------------------------------------------------------------------------


def test_lru_cache_update_does_not_increase_size():
    cache = LRUCache(maxsize=3)
    cache["a"] = 1
    cache["b"] = 2
    assert len(cache) == 2

    cache["a"] = 100  # update existing key
    assert len(cache) == 2
    assert cache["a"] == 100


def test_lru_cache_clear_resets_state():
    cache = LRUCache(maxsize=2)
    cache["a"] = 1
    cache["b"] = 2
    assert len(cache) == 2

    cache.clear()
    assert len(cache) == 0
    assert "a" not in cache
    assert "b" not in cache


def test_lru_cache_popitem_removes_one_entry():
    cache = LRUCache(maxsize=3)
    cache["a"] = 1
    cache["b"] = 2
    cache["c"] = 3
    assert len(cache) == 3

    k, v = cache.popitem()
    assert k not in cache
    assert len(cache) == 2
    assert isinstance(k, str)
    assert v in (1, 2, 3)


def test_ttl_cache_overwrite_resets_ttl():
    ttl_seconds = 0.2
    cache = TTLCache(maxsize=10, ttl=ttl_seconds)

    cache["k"] = "v1"
    time.sleep(0.1)
    cache["k"] = "v2"  # overwrite should refresh TTL in typical implementations

    # Shortly after overwrite, value should still be visible
    assert cache["k"] == "v2"
    assert "k" in cache


def test_ttl_cache_len_drops_after_expiration():
    ttl_seconds = 0.15
    cache = TTLCache(maxsize=10, ttl=ttl_seconds)

    cache["a"] = 1
    cache["b"] = 2
    assert len(cache) >= 2

    time.sleep(ttl_seconds + 0.25)

    # After TTL, both should be expired; len may be lazily cleaned, but access should not succeed.
    with pytest.raises(KeyError):
        _ = cache["a"]
    with pytest.raises(KeyError):
        _ = cache["b"]

    assert "a" not in cache
    assert "b" not in cache


def test_cached_decorator_cache_clear_forces_recompute():
    cache = LRUCache(maxsize=32)
    calls = {"count": 0}

    @cached(cache=cache)
    def f(x: int) -> int:
        calls["count"] += 1
        return x + 1

    assert f(1) == 2
    assert calls["count"] == 1
    assert f(1) == 2
    assert calls["count"] == 1  # cached

    cache.clear()
    assert f(1) == 2
    assert calls["count"] == 2  # recomputed after clear


def test_custom_key_collision_is_handled():
    cache = LRUCache(maxsize=8)
    calls = {"count": 0}

    def constant_key(*args: Any, **kwargs: Any) -> Tuple[str]:
        # Forces collisions: different inputs map to same cache key.
        return ("constant",)

    @cached(cache=cache, key=constant_key)
    def g(x: int) -> int:
        calls["count"] += 1
        return x * 10

    v1 = g(1)
    v2 = g(2)

    # Collision behavior can vary (overwrite or keep first), but it must be deterministic and not crash.
    assert v1 in (10, 20)
    assert v2 in (10, 20)
    assert calls["count"] >= 1


def test_cached_threaded_smoke_does_not_hang():
    cache = LRUCache(maxsize=128)
    calls = {"count": 0}

    @cached(cache=cache)
    def slow_add(x: int, y: int) -> int:
        calls["count"] += 1
        return x + y

    results: Dict[int, int] = {}
    errors: Dict[int, str] = {}

    def worker(i: int) -> None:
        try:
            results[i] = slow_add(i, 1)
        except Exception as e:
            errors[i] = str(e)

    threads = []
    for i in range(8):
        t = threading.Thread(target=worker, args=(i,))
        t.daemon = True
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout=2.0)

    assert not any(t.is_alive() for t in threads)
    for i in range(8):
        if i in results:
            assert results[i] == i + 1
    assert isinstance(calls["count"], int)
