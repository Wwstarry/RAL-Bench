import ast
import importlib.util
import os
import sys
from pathlib import Path

import pytest


TARGET_ENV = "MITMPROXY_TARGET"
TARGET_REFERENCE_VALUE = "reference"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _repo_root() -> Path:
    env_root = os.getenv("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return (_project_root() / "repositories" / "mitmproxy").resolve()


def _pythonpath_root() -> Path:
    """
    mitmproxy uses a flat package layout in the repo, but some repos use src/.
    Add whichever contains the mitmproxy package.
    """
    repo = _repo_root()
    if (repo / "src" / "mitmproxy").is_dir():
        return (repo / "src").resolve()
    return repo.resolve()


def _mitmproxy_pkg_dir() -> Path:
    base = _pythonpath_root()
    pkg = base / "mitmproxy"
    assert pkg.is_dir(), f"Expected mitmproxy package directory at: {pkg}"
    return pkg


def _file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _has_module(modname: str) -> bool:
    return importlib.util.find_spec(modname) is not None


def _ast_has_function(py_path: Path, func_name: str) -> bool:
    tree = ast.parse(_file(py_path))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            return True
    return False


def _ast_has_class(py_path: Path, class_name: str) -> bool:
    tree = ast.parse(_file(py_path))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return True
    return False


def _prepend_import_path():
    sys.path.insert(0, str(_pythonpath_root()))


def test_001_mitmproxy_package_dir_exists():
    _mitmproxy_pkg_dir()


def test_002_top_level_import_mitmproxy():
    _prepend_import_path()
    import mitmproxy  # noqa: F401


def test_003_version_source_file_exists_and_has_version_like_token():
    """
    Do NOT assume mitmproxy exposes __version__ at top-level.
    Instead, require a stable version source file under the package and a version-like token inside.

    This aligns better with how many projects store version information (e.g. version.py, __init__.py, or pyproject).
    """
    pkg = _mitmproxy_pkg_dir()

    candidates = [
        pkg / "version.py",
        pkg / "__init__.py",
    ]

    existing = [p for p in candidates if p.is_file()]
    assert existing, f"Expected one of these to exist: {[str(p) for p in candidates]}"

    text = "\n".join(_file(p).lower() for p in existing)

    # Accept multiple common patterns.
    # Examples: __version__ = "10.0.0", VERSION = "10.0.0", version = "10.0.0"
    import re

    assert (
        re.search(r"__version__\s*=\s*['\"][^'\"]+['\"]", text)
        or re.search(r"\bversion\s*=\s*['\"][^'\"]+['\"]", text)
        or re.search(r"\bversion\b", text)
    ), "Expected a version-like assignment or token in version source files."


def test_004_tools_main_file_exists():
    pkg = _mitmproxy_pkg_dir()
    assert (pkg / "tools" / "main.py").is_file()


def test_005_tools_dump_file_exists():
    pkg = _mitmproxy_pkg_dir()
    assert (pkg / "tools" / "dump.py").is_file()


def test_006_tools_cmdline_file_exists():
    pkg = _mitmproxy_pkg_dir()
    assert (pkg / "tools" / "cmdline.py").is_file()


def test_007_tools_main_defines_mitmdump_function_or_wrapper():
    """
    Anchor: mitmproxy.tools.main.mitmdump should exist.
    If runtime import is blocked by missing mitmproxy_rs, we still enforce the symbol statically.
    """
    pkg = _mitmproxy_pkg_dir()
    main_py = pkg / "tools" / "main.py"
    src = _file(main_py)

    # Prefer AST check; also accept simple textual presence for wrapper patterns.
    assert _ast_has_function(main_py, "mitmdump") or "def mitmdump" in src


def test_008_tools_dump_defines_DumpMaster_class():
    """
    Anchor: mitmproxy.tools.dump.DumpMaster should exist.
    """
    pkg = _mitmproxy_pkg_dir()
    dump_py = pkg / "tools" / "dump.py"
    src = _file(dump_py)

    assert _ast_has_class(dump_py, "DumpMaster") or "class DumpMaster" in src


def test_009_proxy_mode_specs_mentions_ProxyMode():
    """
    Anchor: mitmproxy.proxy.mode_specs is part of the CLI import chain.
    Runtime import may require mitmproxy_rs; we assert the file contains ProxyMode constructs.
    """
    pkg = _mitmproxy_pkg_dir()
    ms_py = pkg / "proxy" / "mode_specs.py"
    assert ms_py.is_file()
    src = _file(ms_py)
    assert "ProxyMode" in src


def test_010_conditional_import_http_module_depends_on_OpenSSL():
    """
    Importing mitmproxy.http may require pyOpenSSL (OpenSSL module) through mitmproxy.certs.
    If OpenSSL is installed, import must succeed.
    If not installed, import must fail with ModuleNotFoundError mentioning OpenSSL.
    """
    _prepend_import_path()
    have_openssl = _has_module("OpenSSL")
    if have_openssl:
        import mitmproxy.http  # noqa: F401
    else:
        with pytest.raises(ModuleNotFoundError) as ei:
            import mitmproxy.http  # noqa: F401
        assert "openssl" in str(ei.value).lower()


def test_011_conditional_import_tools_main_depends_on_mitmproxy_rs():
    """
    Importing mitmproxy.tools.main currently pulls in mitmproxy.proxy.mode_specs,
    which imports mitmproxy_rs. If mitmproxy_rs is installed, import should succeed.
    Otherwise, it should fail with ModuleNotFoundError mentioning mitmproxy_rs.
    """
    _prepend_import_path()
    have_rs = _has_module("mitmproxy_rs")
    if have_rs:
        from mitmproxy.tools import main as tools_main  # noqa: F401
        assert hasattr(tools_main, "mitmdump")
    else:
        with pytest.raises(ModuleNotFoundError) as ei:
            from mitmproxy.tools import main as tools_main  # noqa: F401
        assert "mitmproxy_rs" in str(ei.value).lower()
