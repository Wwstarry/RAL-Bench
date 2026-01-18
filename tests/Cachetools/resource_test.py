import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]

TARGET_ENV = "CACHETOOLS_TARGET"
TARGET_REFERENCE_VALUE = "reference"

target = os.getenv(TARGET_ENV, "generated")

if target == TARGET_REFERENCE_VALUE:
    sys.path.insert(0, str(ROOT_DIR / "repositories" / "cachetools"))
else:
    sys.path.insert(0, str(ROOT_DIR / "generation" / "Cachetools"))

from cachetools import LRUCache, TTLCache  # type: ignore  # noqa: E402


def test_cache_never_exceeds_maxsize_under_load():
    maxsize = 128
    cache = LRUCache(maxsize=maxsize)

    # Insert many more keys than maxsize; internal eviction policy should keep
    # the number of stored entries bounded.
    for i in range(5000):
        cache[f"key-{i}"] = i

    assert len(cache) <= maxsize


def test_ttl_cache_under_continuous_updates():
    maxsize = 256
    cache = TTLCache(maxsize=maxsize, ttl=60.0)

    # Rapidly overwrite a fixed set of keys many times; this should not cause
    # unbounded growth and should keep size within maxsize.
    for i in range(10000):
        key = f"user-{i % 512}"
        cache[key] = i

    assert len(cache) <= maxsize
