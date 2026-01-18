from __future__ import annotations

import datetime as dt
import os
import sys
from pathlib import Path

import psutil  # type: ignore

ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT_ENV = "RACB_REPO_ROOT"


def _select_repo_root() -> Path:
    override = os.environ.get(REPO_ROOT_ENV)
    if override:
        return Path(override).resolve()

    target = os.environ.get("ASTRAL_TARGET", "generated").lower()
    if target == "reference":
        for name in ("Astral", "astral"):
            cand = ROOT / "repositories" / name
            if cand.exists():
                return cand.resolve()
        return (ROOT / "repositories" / "Astral").resolve()
    return (ROOT / "generation" / "Astral").resolve()


REPO_ROOT = _select_repo_root()


def _ensure_import_path(repo_root: Path) -> None:
    src = repo_root / "src"
    sys_path_entry = str(src if src.exists() else repo_root)
    if sys_path_entry not in sys.path:
        sys.path.insert(0, sys_path_entry)


_ensure_import_path(REPO_ROOT)

from astral import LocationInfo  # type: ignore
from astral.sun import sun  # type: ignore


def _london_location() -> LocationInfo:
    return LocationInfo("London", "England", "Europe/London", 51.5074, -0.1278)


def test_resource_usage_smoke() -> None:
    """
    Smoke test: run a representative batch workload and verify
    we can observe process resource info without crashing.

    Note: The benchmark runner measures subprocess resources.
    This test is correctness-oriented only.
    """
    proc = psutil.Process()
    rss_before = proc.memory_info().rss

    loc = _london_location()
    base_date = dt.date(2020, 1, 1)

    for offset in range(60):
        d = base_date + dt.timedelta(days=offset)
        _ = sun(loc.observer, date=d, tzinfo=loc.timezone)

    rss_after = proc.memory_info().rss
    assert rss_before > 0
    assert rss_after > 0
