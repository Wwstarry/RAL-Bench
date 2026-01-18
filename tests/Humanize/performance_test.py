from __future__ import annotations

import os
import sys
import time
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

target = os.environ.get("HUMANIZE_TARGET", "reference").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "humanize"
else:
    REPO_ROOT = ROOT / "generation" / "Humanize"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

src_dir = REPO_ROOT / "src"
if src_dir.exists() and str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


def _install_version_stub() -> None:
    """Install a minimal humanize._version stub if missing."""
    name = "humanize._version"
    if name in sys.modules:
        return

    mod = types.ModuleType(name)
    mod.__dict__["__version__"] = "0.0.0-benchmark"
    sys.modules[name] = mod


_install_version_stub()

import humanize  # type: ignore  # noqa: E402


def test_many_intcomma_calls() -> None:
    """Benchmark-style smoke test for intcomma."""
    start = time.perf_counter()
    for i in range(20000):
        humanize.intcomma(i)
    elapsed = time.perf_counter() - start

    # Must be reasonably fast (reference is typically well below this bound).
    assert elapsed < 0.5
