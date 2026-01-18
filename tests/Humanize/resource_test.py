from __future__ import annotations

import os
import sys
import types
from pathlib import Path
from datetime import datetime, timedelta

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


def test_report_generation_pipeline() -> None:
    """
    Integration-like test: simulate a log/report formatting pipeline.
    Ensures humanize functions can be composed.
    """

    base = {
        "bytes_sent": 123456789,
        "items_processed": 2345,
        "start": datetime(2020, 1, 1, 12, 0, 0),
        "end": datetime(2020, 1, 1, 14, 30, 0),
    }

    report = {
        "size_human": humanize.naturalsize(base["bytes_sent"]),
        "items": humanize.intcomma(base["items_processed"]),
        "duration": humanize.naturaldelta(base["end"] - base["start"]),
        "finished": humanize.naturaltime(base["end"], when=base["end"]),
    }

    assert "MB" in report["size_human"] or "GB" in report["size_human"]
    assert "," in report["items"]
    assert "hours" in report["duration"]
    assert "now" in report["finished"]
