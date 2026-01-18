import ast
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

TARGET_ENV = "FAIL2BAN_TARGET"
TARGET_REFERENCE_VALUE = "reference"


def _project_root() -> Path:
    # tests/Fail2ban/*.py -> project root
    return Path(__file__).resolve().parents[2]


def _resolve_repo_root() -> Path:
    """
    Reference mode uses RACB_REPO_ROOT if provided (measure_reference sets it).
    Otherwise ROOT/repositories/fail2ban.
    Generated mode uses ROOT/generation/Fail2ban.
    """
    root = _project_root()
    target = os.getenv(TARGET_ENV, TARGET_REFERENCE_VALUE)

    if target == TARGET_REFERENCE_VALUE:
        rr = os.getenv("RACB_REPO_ROOT")
        repo = Path(rr).resolve() if rr else (root / "repositories" / "fail2ban").resolve()
    else:
        repo = (root / "generation" / "Fail2ban").resolve()

    # Support src layout if present.
    if (repo / "src" / "fail2ban").is_dir():
        return (repo / "src").resolve()
    return repo


def _pkg_dir() -> Path:
    base = _resolve_repo_root()
    pkg = base / "fail2ban"
    assert pkg.is_dir(), f"Expected fail2ban package directory at: {pkg}"
    return pkg


def _prepend_import_path():
    sys.path.insert(0, str(_resolve_repo_root()))


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def _has_module(modname: str) -> bool:
    return importlib.util.find_spec(modname) is not None


def _ast_has_class(py_path: Path, class_name: str) -> bool:
    tree = ast.parse(_read_text(py_path))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return True
    return False


def _ast_has_function(py_path: Path, func_name: str) -> bool:
    tree = ast.parse(_read_text(py_path))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            return True
    return False


def _run_script_help(script_path: Path, timeout_s: int = 25) -> subprocess.CompletedProcess:
    """
    Run: python <script> -h (or --help)
    This must not start the daemon; scripts should exit quickly on help.
    """
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    # Ensure local repo import works.
    env["PYTHONPATH"] = str(_resolve_repo_root()) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return subprocess.run(
        [sys.executable, str(script_path), "-h"],
        text=True,
        input="",
        capture_output=True,
        timeout=timeout_s,
        env=env,
    )


def _out(p: subprocess.CompletedProcess) -> str:
    return (p.stdout + "\n" + p.stderr).lower()


def test_001_package_dir_exists():
    _pkg_dir()


def test_002_core_server_module_files_exist():
    pkg = _pkg_dir()
    assert (pkg / "server" / "jail.py").is_file(), "Expected fail2ban/server/jail.py"
    assert (pkg / "server" / "filter.py").is_file(), "Expected fail2ban/server/filter.py"


def test_003_jail_class_exists_statically():
    jail_py = _pkg_dir() / "server" / "jail.py"
    src = _read_text(jail_py)
    assert _ast_has_class(jail_py, "Jail") or "class Jail" in src


def test_004_filter_core_symbols_exist_statically():
    """
    Do not assume helper names like isValidIP/searchIP (they vary across versions).
    Instead, require stable core anchors in fail2ban.server.filter:
      - A Filter class (or similarly named core filter object), OR
      - presence of key tokens that indicate regex-driven filtering (failregex/<HOST>).
    """
    filter_py = _pkg_dir() / "server" / "filter.py"
    src = _read_text(filter_py)

    has_filter_class = _ast_has_class(filter_py, "Filter") or ("class Filter" in src)
    has_regex_tokens = ("failregex" in src.lower()) or ("<host>" in src.lower())

    assert has_filter_class or has_regex_tokens, "Expected core filter anchors (Filter class or failregex/<HOST> tokens)."


def test_005_config_jail_conf_exists():
    base = _resolve_repo_root()
    cfg = base / "config" / "jail.conf"
    assert cfg.is_file(), "Expected config/jail.conf to exist"


def test_006_bin_scripts_exist():
    base = _resolve_repo_root()
    b = base / "bin"
    assert b.is_dir(), "Expected bin/ directory"
    assert (b / "fail2ban-client").is_file(), "Expected bin/fail2ban-client"
    assert (b / "fail2ban-server").is_file(), "Expected bin/fail2ban-server"
    assert (b / "fail2ban-regex").is_file(), "Expected bin/fail2ban-regex"


def test_007_import_fail2ban_top_level_is_reasonable():
    """
    On some platforms, Fail2Ban may have POSIX-specific optional imports.
    We accept either:
      - successful import, OR
      - ModuleNotFoundError mentioning common POSIX-only modules.
    """
    _prepend_import_path()
    try:
        import fail2ban  # noqa: F401
    except ModuleNotFoundError as e:
        msg = str(e).lower()
        # keep this tight: only allow known platform gaps
        assert any(k in msg for k in ["pwd", "grp", "resource"]), f"Unexpected import failure: {e}"


def test_008_import_jail_if_possible_else_allow_platform_gap():
    _prepend_import_path()
    try:
        from fail2ban.server.jail import Jail  # noqa: F401
    except ModuleNotFoundError as e:
        msg = str(e).lower()
        # Windows/POSIX gaps that are expected for reference when running on Windows.
        assert any(k in msg for k in ["pwd", "grp", "resource", "fcntl"]), f"Unexpected import failure: {e}"


def test_009_import_filter_and_basic_behavior_if_possible():
    _prepend_import_path()
    try:
        from fail2ban.server import filter as f
    except ModuleNotFoundError as e:
        msg = str(e).lower()
        assert any(k in msg for k in ["pwd", "grp", "resource", "fcntl"]), f"Unexpected import failure: {e}"
        return

    # If import works, ensure the module exposes a core Filter-like object or regex constants.
    if hasattr(f, "Filter"):
        assert callable(getattr(f, "Filter"))
    else:
        src = _read_text(_pkg_dir() / "server" / "filter.py").lower()
        assert ("failregex" in src) or ("<host>" in src)


def test_010_fail2ban_client_help_exits_quickly():
    base = _resolve_repo_root()
    p = _run_script_help(base / "bin" / "fail2ban-client", timeout_s=25)
    out = _out(p)
    # Return codes vary; require that output looks like help/usage.
    assert ("usage" in out) or ("options" in out) or ("fail2ban-client" in out)


def test_011_fail2ban_regex_help_exits_quickly():
    base = _resolve_repo_root()
    p = _run_script_help(base / "bin" / "fail2ban-regex", timeout_s=25)
    out = _out(p)
    assert ("usage" in out) or ("options" in out) or ("fail2ban-regex" in out)


def test_012_fail2ban_regex_matches_simple_pattern_offline():
    """
    Offline-only functional check:
    - Create a temp log with repeated failure lines.
    - Run fail2ban-regex <LOG> <REGEX>
    - Assert output indicates it processed lines and found matches.
    """
    base = _resolve_repo_root()
    script = base / "bin" / "fail2ban-regex"

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONPATH"] = str(_resolve_repo_root()) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

    with tempfile.TemporaryDirectory(prefix="racb_fail2ban_") as td:
        logp = Path(td) / "auth.log"
        logp.write_text(
            "\n".join(
                [
                    "Failed password for invalid user root from 203.0.113.5 port 2222 ssh2",
                    "Failed password for invalid user admin from 203.0.113.5 port 2223 ssh2",
                    "Accepted password for user ok from 198.51.100.2 port 3333 ssh2",
                    "Failed password for invalid user test from 203.0.113.9 port 4444 ssh2",
                ]
            ),
            encoding="utf-8",
        )

        # Use a very simple regex (do not rely on <HOST> substitutions).
        regex = r"Failed password"
        p = subprocess.run(
            [sys.executable, str(script), str(logp), regex],
            text=True,
            input="",
            capture_output=True,
            timeout=30,
            env=env,
        )
        out = _out(p)

        # Must not hang; and should show it processed lines.
        assert ("line" in out) or ("lines" in out)
        # Try to detect match reporting; be tolerant across versions.
        assert ("match" in out) or ("found" in out) or ("failregex" in out)
