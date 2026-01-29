"""
A lightweight compatibility wrapper around the real third-party `requests` package.

This repository is evaluated against the public APIs of the `requests` library.
The dependency `requests` is installed in the environment. However, since this
repository also provides a top-level `requests` package, we must delegate to the
installed package to avoid shadowing it.

This module loads the real `requests` distribution from site-packages under an
internal name and re-exports its public interface.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from types import ModuleType


def _load_real_requests() -> ModuleType:
    """
    Locate and load the *installed* third-party `requests` package, even though
    this repository provides a `requests` package that would normally shadow it.

    Strategy:
    - Search sys.path entries excluding this repository's own directory.
    - Find a `requests/__init__.py` that is not this file.
    - Load it as module name `_real_requests` (and its submodules as `_real_requests.*`).
    """
    this_dir = os.path.dirname(__file__)
    this_init = os.path.abspath(__file__)

    candidate_init = None
    for base in sys.path:
        if not base:
            continue
        # Skip our own package directory and its parent
        try:
            if os.path.samefile(os.path.abspath(base), os.path.abspath(os.path.dirname(this_dir))):
                continue
        except Exception:
            # On some platforms/path types samefile may fail; keep conservative
            pass

        cand = os.path.join(base, "requests", "__init__.py")
        if os.path.isfile(cand):
            if os.path.abspath(cand) != this_init:
                candidate_init = cand
                break

    if not candidate_init:
        raise ImportError(
            "Could not locate the installed third-party 'requests' package on sys.path "
            "(it may not be installed)."
        )

    spec = importlib.util.spec_from_file_location(
        "_real_requests",
        candidate_init,
        submodule_search_locations=[os.path.dirname(candidate_init)],
    )
    if spec is None or spec.loader is None:
        raise ImportError("Failed to create import spec for real 'requests'.")

    module = importlib.util.module_from_spec(spec)
    # Ensure imports of `_real_requests.*` during initialization work
    sys.modules["_real_requests"] = module
    spec.loader.exec_module(module)
    return module


_real = _load_real_requests()


def _alias_submodule(public_name: str, real_name: str) -> None:
    """
    Expose `_real_requests.<real_name>` as `requests.<public_name>` in sys.modules
    so that `import requests.sessions` works.
    """
    try:
        sub = getattr(_real, real_name)
    except Exception:
        # Try importing it from the real package
        import importlib

        sub = importlib.import_module(f"_real_requests.{real_name}")
    sys.modules[f"{__name__}.{public_name}"] = sub


# Re-export main attributes
for k, v in _real.__dict__.items():
    if k.startswith("__") and k not in ("__version__",):
        continue
    globals()[k] = v

# Ensure key submodules are available under our package namespace
for _sub in ("api", "sessions", "models", "auth", "exceptions", "adapters", "cookies", "utils", "status_codes"):
    _alias_submodule(_sub, _sub)

# Convenience: ensure `requests.request` etc are present
__all__ = getattr(_real, "__all__", None) or [k for k in globals().keys() if not k.startswith("_")]