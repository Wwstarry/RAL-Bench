import ast
import importlib
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


def _project_root() -> Path:
    # tests/Glances/functional_test.py -> parents[2] == project root
    return Path(__file__).resolve().parents[2]


def _repo_root() -> Path:
    return _project_root() / "repositories" / "glances"


def _pkg_root() -> Path:
    return _repo_root() / "glances"


def _ensure_repo_on_syspath() -> None:
    repo = _repo_root()
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))


def _iter_py_modules_from_fs(pkg_dir: Path, pkg_prefix: str) -> List[str]:
    """
    Discover importable module names by filesystem layout.
    This does NOT import modules (safe under Py3.9 even if annotations would crash on import).
    """
    out: List[str] = []
    if not pkg_dir.exists():
        return out

    for p in pkg_dir.rglob("*.py"):
        if p.name == "__init__.py":
            continue
        rel = p.relative_to(pkg_dir).with_suffix("")
        parts = list(rel.parts)
        mod = pkg_prefix + "." + ".".join(parts)
        out.append(mod)

    out.sort()
    return out


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def _iter_py_files(pkg_dir: Path) -> List[Path]:
    if not pkg_dir.exists():
        return []
    files = [p for p in pkg_dir.rglob("*.py") if p.is_file()]
    files.sort()
    return files


def _best_effort_import(mod_names: Iterable[str], target_success: int) -> Tuple[List[str], Dict[str, str]]:
    """
    Try importing module names until we hit target_success.
    Failures are collected but do not fail unless success < target_success.
    """
    ok: List[str] = []
    fail: Dict[str, str] = {}

    for m in mod_names:
        if len(ok) >= target_success:
            break
        try:
            importlib.import_module(m)
            ok.append(m)
        except Exception as e:  # noqa: BLE001
            fail[m] = f"{type(e).__name__}: {e}"

    return ok, fail


def _import_glances_base() -> None:
    _ensure_repo_on_syspath()
    import glances  # noqa: F401


def _plugins_dir() -> Path:
    return _pkg_root() / "plugins"


def _exports_dir() -> Path:
    return _pkg_root() / "exports"


def _discover_plugins() -> List[str]:
    return _iter_py_modules_from_fs(_plugins_dir(), "glances.plugins")


def _discover_exports() -> List[str]:
    return _iter_py_modules_from_fs(_exports_dir(), "glances.exports")


def test_001_repo_layout_exists() -> None:
    assert _repo_root().exists(), f"missing repo root: {_repo_root()}"
    assert _pkg_root().exists(), f"missing package root: {_pkg_root()}"
    assert (_pkg_root() / "__init__.py").exists(), "glances package missing __init__.py"


def test_002_import_glances_base_module() -> None:
    _import_glances_base()


def test_003_version_attribute_is_present() -> None:
    _ensure_repo_on_syspath()
    import glances

    ver = getattr(glances, "__version__", None)
    assert isinstance(ver, str) and ver.strip(), f"unexpected __version__: {ver!r}"


def test_004_globals_platform_flags_are_consistent() -> None:
    _ensure_repo_on_syspath()
    from glances import globals as g

    assert isinstance(g.WINDOWS, bool)
    assert isinstance(g.LINUX, bool)
    # Your environment is Windows.
    assert g.WINDOWS is True, "expected WINDOWS=True on win32"


def test_005_safe_makedirs_creates_nested_dir(tmp_path: Path) -> None:
    _ensure_repo_on_syspath()
    from glances.globals import safe_makedirs

    d = tmp_path / "a" / "b" / "c"
    safe_makedirs(str(d))
    assert d.exists() and d.is_dir()
    # Idempotent
    safe_makedirs(str(d))
    assert d.exists() and d.is_dir()


def test_006_json_dumps_handles_datetime() -> None:
    _ensure_repo_on_syspath()
    from datetime import datetime

    from glances import globals as g

    payload = {"t": datetime.utcnow()}
    out = g.json.dumps(payload)
    assert out is not None
    assert isinstance(out, (str, bytes))


def test_007_plugins_are_discoverable_from_filesystem() -> None:
    _import_glances_base()
    plugins = _discover_plugins()
    assert len(plugins) >= 5, f"too few plugin modules discovered: {len(plugins)}"


def test_008_exports_are_discoverable_from_filesystem() -> None:
    _import_glances_base()
    exports = _discover_exports()
    assert len(exports) >= 1, "no export modules discovered"


def test_009_can_import_at_least_five_plugins_best_effort() -> None:
    """
    On Python 3.9, some Glances plugin modules may fail to import because:
    - runtime-evaluated PEP604 unions (A | B) appear in type annotations
    - optional dependencies are missing (docker/podman/etc.)
    Therefore we require a modest minimum number of successfully imported plugins.
    """
    _import_glances_base()
    plugins = _discover_plugins()

    min_success = 5
    ok, fail = _best_effort_import(plugins, target_success=10)  # try up to 10, but require >=5
    assert len(ok) >= min_success, (
        f"only imported {len(ok)}/{min_success} required plugins.\n"
        f"imported_ok={ok}\n"
        f"first_failures={list(fail.items())[:15]}"
    )


def test_010_can_import_at_least_one_export_best_effort() -> None:
    _import_glances_base()
    exports = _discover_exports()

    ok, fail = _best_effort_import(exports, target_success=2)
    assert len(ok) >= 1, (
        "no exports importable.\n"
        f"first_failures={list(fail.items())[:15]}"
    )


def test_011_system_exec_returns_string_even_on_error() -> None:
    _ensure_repo_on_syspath()
    from glances.globals import system_exec

    out = system_exec("definitely_not_a_real_command_12345")
    assert isinstance(out, str)
    assert out != ""


# def test_012_plugins_source_files_parse_with_ast() -> None:
#     """
#     Basic sanity on plugin source files (parsing works, no empty files).
#     This does not import them.
#     """
#     _import_glances_base()
#     d = _plugins_dir()
#     assert d.exists()
#     py_files = _iter_py_files(d)
#     assert len(py_files) >= 5

#     checked = 0
#     for f in py_files[:40]:
#         txt = _read_text(f)
#         assert len(txt.strip()) > 0, f"empty file: {f}"
#         ast.parse(txt)
#         checked += 1

#     assert checked >= 5


def test_013_plugins_directory_has_expected_subpackages() -> None:
    """
    Structural check: plugin tree should contain common subdirs.
    """
    _import_glances_base()
    d = _plugins_dir()
    assert (d / "plugin").exists(), "expected plugins/plugin subpackage"
