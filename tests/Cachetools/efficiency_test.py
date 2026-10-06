import os
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]

TARGET_ENV = "CACHETOOLS_TARGET"
TARGET_REFERENCE_VALUE = "reference"

target = os.getenv(TARGET_ENV, "generated")

if target == TARGET_REFERENCE_VALUE:
    sys.path.insert(0, str(ROOT_DIR / "repositories" / "cachetools"))
else:
    sys.path.insert(0, str(ROOT_DIR / "generation" / "Cachetools"))

from cachetools import LRUCache, cached  # type: ignore  # noqa: E402


def test_many_cached_calls_performance():
    cache = LRUCache(maxsize=1024)

    call_count = {"count": 0}

    @cached(cache=cache)
    def heavy(x: int) -> int:
        call_count["count"] += 1
        # Simulate some non-trivial work
        total = 0
        for i in range(50):
            total += (x + i) * (x - i)
        return total

    start = time.perf_counter()

    # Many calls, most of which should end up using cached results
    for i in range(500):
        for j in (1, 2, 3, 4, 5):
            heavy(j)

    elapsed = time.perf_counter() - start

    # Sanity checks:
    # - Result is consistent
    # - Number of actual computations is bounded by cache size / distinct keys
    assert heavy(1) == heavy(1)
    assert call_count["count"] <= 100

    # Do not assert on elapsed time here; it is only used for baseline metrics.
    _ = elapsed
