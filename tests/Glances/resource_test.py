import gc
import importlib
import sys
import tracemalloc
from pathlib import Path
from typing import Dict, List, Tuple


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _repo_root() -> Path:
    return _project_root() / "repositories" / "glances"


def _pkg_root() -> Path:
    return _repo_root() / "glances"


def _ensure_repo_on_syspath() -> None:
    repo = _repo_root()
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))


def _discover_modules(dir_path: Path, prefix: str) -> List[str]:
    mods: List[str] = []
    if not dir_path.exists():
        return mods
    for p in dir_path.rglob("*.py"):
        if p.name == "__init__.py":
            continue
        rel = p.relative_to(dir_path).with_suffix("")
        mods.append(prefix + "." + ".".join(rel.parts))
    mods.sort()
    return mods


def _best_effort_import_some(mods: List[str], want: int) -> Tuple[List[str], Dict[str, str]]:
    ok: List[str] = []
    fail: Dict[str, str] = {}
    for m in mods:
        if len(ok) >= want:
            break
        try:
            importlib.import_module(m)
            ok.append(m)
        except Exception as e:  # noqa: BLE001
            fail[m] = f"{type(e).__name__}: {e}"
    return ok, fail


def test_resource_reloading_plugins_does_not_explode_python_memory() -> None:
    """
    Resource proxy: repeated reloads should not keep allocating unbounded memory (Python-level).
    Uses tracemalloc for stability across OSes.
    """
    _ensure_repo_on_syspath()
    import glances  # noqa: F401

    plugins_dir = _pkg_root() / "plugins"
    mods = _discover_modules(plugins_dir, "glances.plugins")
    assert len(mods) >= 5

    ok, fail = _best_effort_import_some(mods, want=10)
    assert len(ok) >= 5, f"only {len(ok)} plugin modules importable; failures={list(fail.items())[:10]}"

    tracemalloc.start()
    gc.collect()
    snap0 = tracemalloc.take_snapshot()

    loops = 30
    for _ in range(loops):
        for m in ok:
            importlib.reload(sys.modules[m])
        gc.collect()

    snap1 = tracemalloc.take_snapshot()
    stats = snap1.compare_to(snap0, "lineno")
    allocated = sum(s.size_diff for s in stats)

    assert allocated < 15 * 1024 * 1024, f"excessive Python allocations: {allocated / (1024 * 1024):.2f} MB"
