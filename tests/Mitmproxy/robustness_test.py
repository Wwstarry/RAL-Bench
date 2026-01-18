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
    repo = _repo_root()
    if (repo / "src" / "mitmproxy").is_dir():
        return (repo / "src").resolve()
    return repo.resolve()


def _prepend_import_path():
    sys.path.insert(0, str(_pythonpath_root()))


def _has_module(modname: str) -> bool:
    return importlib.util.find_spec(modname) is not None


def test_001_import_mitmproxy_is_stable():
    _prepend_import_path()
    import mitmproxy  # noqa: F401
    import mitmproxy as mitmproxy_again  # noqa: F401


def test_002_missing_OpenSSL_is_handled_deterministically():
    """
    If OpenSSL is missing, importing mitmproxy.http should fail with ModuleNotFoundError(OpenSSL),
    not with an unrelated exception or a hang.
    """
    _prepend_import_path()
    if _has_module("OpenSSL"):
        import mitmproxy.http  # noqa: F401
    else:
        with pytest.raises(ModuleNotFoundError) as ei:
            import mitmproxy.http  # noqa: F401
        assert "openssl" in str(ei.value).lower()


def test_003_missing_mitmproxy_rs_is_handled_deterministically():
    """
    If mitmproxy_rs is missing, importing mitmproxy.tools.main should fail with ModuleNotFoundError(mitmproxy_rs).
    """
    _prepend_import_path()
    if _has_module("mitmproxy_rs"):
        from mitmproxy.tools import main as tools_main  # noqa: F401
        assert hasattr(tools_main, "mitmdump")
    else:
        with pytest.raises(ModuleNotFoundError) as ei:
            from mitmproxy.tools import main as tools_main  # noqa: F401
        assert "mitmproxy_rs" in str(ei.value).lower()


def test_004_static_cmdline_spec_file_exists_and_nonempty():
    _prepend_import_path()
    pkg = Path(_pythonpath_root()) / "mitmproxy"
    cmdline_py = pkg / "tools" / "cmdline.py"
    assert cmdline_py.is_file()
    assert cmdline_py.stat().st_size > 0


def test_005_static_mode_specs_mentions_examples():
    _prepend_import_path()
    pkg = Path(_pythonpath_root()) / "mitmproxy"
    ms_py = pkg / "proxy" / "mode_specs.py"
    assert ms_py.is_file()
    txt = ms_py.read_text(encoding="utf-8", errors="replace").lower()
    # The file documents mode specs such as "regular" / "reverse:" / "socks5".
    assert "regular" in txt and "reverse" in txt
