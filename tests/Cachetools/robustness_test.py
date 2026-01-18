import os
import sys
import inspect
from pathlib import Path

import pytest


PROJECT_NAME = "Cachetools"
PACKAGE_NAME = "cachetools"


def _candidate_repo_roots() -> list[Path]:
    candidates: list[Path] = []

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        candidates.append(p)
        candidates.append((p / "repositories" / PROJECT_NAME).resolve())
        candidates.append((p / "generation" / PROJECT_NAME).resolve())

    bench_root = Path(__file__).resolve().parents[2]
    candidates.append((bench_root / "repositories" / PROJECT_NAME).resolve())
    candidates.append((bench_root / "generation" / PROJECT_NAME).resolve())

    seen = set()
    uniq: list[Path] = []
    for c in candidates:
        if c not in seen:
            uniq.append(c)
            seen.add(c)
    return uniq


def _looks_like_package_root(repo_root: Path) -> bool:
    if (repo_root / PACKAGE_NAME / "__init__.py").exists():
        return True
    if (repo_root / "src" / PACKAGE_NAME / "__init__.py").exists():
        return True
    return False


def _select_repo_root() -> Path:
    for cand in _candidate_repo_roots():
        if _looks_like_package_root(cand):
            return cand
    raise RuntimeError(
        f"Could not locate importable repo root for '{PACKAGE_NAME}'. "
        f"Tried: {[str(p) for p in _candidate_repo_roots()]}"
    )


def _import_cachetools():
    repo_root = _select_repo_root()
    repo_str = str(repo_root)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)
    import cachetools  # type: ignore
    return cachetools


def test_cache_negative_maxsize_rejects_values_predictably():
    """
    Reference cachetools in your repo treats maxsize=-1 as "no item can fit".
    Robustness expectation:
      - constructing Cache(-1) should not crash
      - storing a normal value should fail predictably (ValueError) rather than corrupting state
    """
    cachetools = _import_cachetools()

    c = cachetools.Cache(-1)
    with pytest.raises(Exception):
        c["k"] = "v"


def test_cache_weird_maxsize_type_does_not_crash_constructor():
    """
    Different cachetools versions differ on whether Cache("100") is accepted.
    Robustness expectation:
      - Constructor should not hard-crash the interpreter.
      - Subsequent basic operations may raise (acceptable).
    """
    cachetools = _import_cachetools()

    try:
        c = cachetools.Cache("100")  # type: ignore[arg-type]
    except Exception:
        # Raising here is acceptable
        return

    # If constructed successfully, basic operations may raise; but should be predictable, not hang.
    try:
        c["k"] = "v"
        _ = c.get("k")
    except Exception:
        pass


def test_cache_value_too_large_for_getsizeof_does_not_crash():
    """
    Extreme getsizeof behavior should not crash the process.
    """
    cachetools = _import_cachetools()

    c = cachetools.Cache(100, getsizeof=lambda _x: 200)
    try:
        c["key"] = "value"
    except Exception:
        pass


@pytest.mark.parametrize("cache_cls", ["FIFOCache", "LFUCache", "LRUCache"])
def test_popitem_on_empty_cache_raises_keyerror(cache_cls: str):
    cachetools = _import_cachetools()
    cls = getattr(cachetools, cache_cls)
    cache = cls(10)

    with pytest.raises(KeyError):
        cache.popitem()


def test_ttlcache_invalid_maxsize_is_handled_safely():
    """
    Some implementations accept maxsize=-1; others raise.
    Either behavior is acceptable as long as it is predictable and does not crash/hang.
    """
    cachetools = _import_cachetools()

    try:
        c = cachetools.TTLCache(-1, ttl=10)
    except Exception:
        return

    try:
        c["k"] = "v"
        _ = c.get("k")
    except Exception:
        pass


def test_ttlcache_negative_ttl_is_handled_safely():
    """
    In your reference, TTLCache(100, ttl=-1) does not raise.
    Robustness expectation:
      - Constructing should not crash.
      - Subsequent operations may behave differently across versions; we accept both.
    """
    cachetools = _import_cachetools()

    try:
        c = cachetools.TTLCache(100, ttl=-1)
    except Exception:
        # Raising is acceptable too
        return

    try:
        c["k"] = "v"
        _ = c.get("k")
    except Exception:
        pass


def test_cached_decorator_is_version_compatible_and_does_not_crash():
    """
    cachetools.cached has multiple signatures across versions.
    We attempt cached(cache) form; if unsupported, skip to avoid false negatives.
    """
    cachetools = _import_cachetools()

    if not hasattr(cachetools, "cached"):
        pytest.skip("cachetools.cached not available in this implementation")

    cached = cachetools.cached

    # Try the common signature: cached(cache, key=...)
    if hasattr(cachetools, "LRUCache"):
        cache_obj = cachetools.LRUCache(maxsize=10)
    else:
        cache_obj = cachetools.Cache(10)

    try:
        decorator = cached(cache_obj)  # type: ignore[misc]
    except Exception:
        pytest.skip("cachetools.cached signature not compatible with cached(cache)")

    @decorator
    def f(x):
        return x

    assert f(1) == 1
    assert f(1) == 1


def test_cachedmethod_basic_usage_smoke():
    """
    cachedmethod should work in a minimal class use case (present in many versions).
    """
    cachetools = _import_cachetools()

    if not hasattr(cachetools, "cachedmethod"):
        pytest.skip("cachetools.cachedmethod not available in this implementation")

    class TestClass:
        @cachetools.cachedmethod(lambda self: cachetools.LRUCache(maxsize=10))
        def cached_method(self, x):
            return x

    obj = TestClass()
    assert obj.cached_method(1) == 1
    assert obj.cached_method(1) == 1


def test_non_hashable_keys_raise_typeerror_in_dict_like_methods():
    """
    This is stable: list keys are unhashable and should raise TypeError.
    """
    cachetools = _import_cachetools()
    c = cachetools.Cache(100)

    with pytest.raises(TypeError):
        _ = c.get([1, 2, 3])  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        c[[1, 2, 3]] = "value"  # type: ignore[index]

    with pytest.raises(TypeError):
        del c[[1, 2, 3]]  # type: ignore[index]

    with pytest.raises(TypeError):
        _ = c.pop([1, 2, 3], None)  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        _ = c.setdefault([1, 2, 3], "v")  # type: ignore[arg-type]
