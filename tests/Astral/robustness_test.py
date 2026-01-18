from __future__ import annotations

import datetime as dt
import os
import sys
from pathlib import Path

import pytest

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


def test_robustness_rejects_invalid_observer() -> None:
    """
    Robustness: invalid observer input should raise quickly,
    not hang or silently return nonsense.
    """
    with pytest.raises(Exception):
        _ = sun(None, date=dt.date(2020, 1, 1), tzinfo="UTC")  # type: ignore[arg-type]


def test_robustness_invalid_date_type() -> None:
    """Robustness: invalid date type should raise."""
    loc = LocationInfo("London", "England", "Europe/London", 51.5074, -0.1278)
    with pytest.raises(Exception):
        _ = sun(loc.observer, date="2020-01-01", tzinfo=loc.timezone)  # type: ignore[arg-type]


def test_robustness_invalid_timezone() -> None:
    """Robustness: invalid tzinfo should raise or be rejected."""
    loc = LocationInfo("London", "England", "Europe/London", 51.5074, -0.1278)
    with pytest.raises(Exception):
        _ = sun(loc.observer, date=dt.date(2020, 1, 1), tzinfo="Not/A_Timezone")
