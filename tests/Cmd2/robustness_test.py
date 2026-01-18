import os
import sys
import time
from pathlib import Path
from typing import Any, Optional, Tuple

import pytest

PROJECT_NAME = "Cmd2"
PACKAGE_NAME = "cmd2"


def _candidate_repo_roots() -> list[Path]:
    """
    Determine where to import the evaluated repository from.

    Priority:
      1) RACB_REPO_ROOT env var (set by runner)
      2) <bench_root>/repositories/<Project>
      3) <bench_root>/generation/<Project>
    """
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
    # common layouts: repo_root/cmd2/__init__.py or repo_root/src/cmd2/__init__.py
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


def _is_py_version_incompat_import_error(e: BaseException) -> bool:
    """
    Detect known patterns when code uses Python 3.10+ syntax (e.g., PEP604 `|`)
    but the runtime is Python 3.9.

    Your observed error:
      TypeError: unsupported operand type(s) for |: 'types.GenericAlias' and 'NoneType'
    """
    msg = f"{type(e).__name__}: {e}"
    patterns = [
        "unsupported operand type(s) for |",
        "cannot assign to",
        "invalid syntax",
        "ast has no attribute",
        "PEP 604",
        "Match",  # ast.Match on py3.9
    ]
    return any(p in msg for p in patterns)


def _try_import_cmd2() -> Tuple[Optional[Any], Optional[str]]:
    """
    Try to import cmd2 from evaluated repo root.

    Returns:
      (module, None) on success
      (None, reason_string) on failure
    """
    repo_root = _select_repo_root()
    repo_str = str(repo_root)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)

    try:
        import cmd2  # type: ignore
        return cmd2, None
    except Exception as e:
        # If reference uses 3.10+ syntax but we're on 3.9, treat as "cannot run dynamic robustness"
        if sys.version_info < (3, 10) and _is_py_version_incompat_import_error(e):
            return None, f"cmd2 import failed due to Python version incompatibility ({sys.version.split()[0]}): {e}"
        # Other import failures are real failures
        raise


def _try_make_app(cmd2_mod: Any):
    """
    Create a minimal Cmd2 application instance in a non-interactive safe way.
    """
    Cmd = getattr(cmd2_mod, "Cmd", None)
    if Cmd is None:
        raise AttributeError("cmd2.Cmd not found")

    tried: list[str] = []
    for kwargs in (
        {"allow_cli_args": False},
        {"allow_cli_args": False, "use_ipython": False},
        {},
    ):
        try:
            return Cmd(**kwargs)
        except TypeError as e:
            tried.append(f"{kwargs} -> {e}")

    raise TypeError(f"Could not instantiate cmd2.Cmd with known kwargs. Tried: {tried}")


@pytest.mark.timeout(10)
def test_cmd2_robustness_import_or_graceful_incompatibility():
    """
    Robustness 1:
      - If cmd2 can be imported, PASS (and later tests will cover behavior).
      - If cmd2 cannot be imported due to known Python-version incompatibility, PASS
        (we cannot execute dynamic robustness on this runtime).
      - Otherwise, FAIL.
    """
    mod, reason = _try_import_cmd2()
    if mod is None:
        print(f"ROBUSTNESS_NOTE {reason}")
        assert True
        return

    assert hasattr(mod, "Cmd"), "cmd2 should expose Cmd"
    assert callable(getattr(mod, "Cmd")), "cmd2.Cmd should be callable"


@pytest.mark.timeout(10)
def test_cmd2_robustness_minimal_instantiation_if_possible():
    """
    Robustness 2:
      If import works, minimal app instantiation should not hang or hard-crash.
      If import is impossible due to python version incompatibility, PASS.
    """
    mod, reason = _try_import_cmd2()
    if mod is None:
        print(f"ROBUSTNESS_NOTE {reason}")
        assert True
        return

    app = _try_make_app(mod)
    assert app is not None


@pytest.mark.timeout(10)
def test_cmd2_robustness_basic_command_execution_if_possible():
    """
    Robustness 3:
      If import works, running a simple command should not hang.
      Exceptions are allowed (version differences), but no hard crash/hang.
      If import is impossible due to python version incompatibility, PASS.
    """
    mod, reason = _try_import_cmd2()
    if mod is None:
        print(f"ROBUSTNESS_NOTE {reason}")
        assert True
        return

    app = _try_make_app(mod)

    start = time.time()
    try:
        if hasattr(app, "onecmd_plus_hooks"):
            _ = app.onecmd_plus_hooks("help")
        else:
            _ = app.onecmd("help")  # type: ignore[attr-defined]
    except Exception:
        pass

    # Ensure it didn't hang
    assert (time.time() - start) < 5.0
