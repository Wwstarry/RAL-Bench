from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Repo root resolution (RACB-compatible + local fallback)
# ---------------------------------------------------------------------------

PACKAGE_NAME = "pendulum"

_racb_root = os.environ.get("RACB_REPO_ROOT", "").strip()
if _racb_root:
    REPO_ROOT = Path(_racb_root).resolve()
else:
    ROOT = Path(__file__).resolve().parents[2]
    target = os.environ.get("PENDULUM_TARGET", "reference").lower()
    if target == "reference":
        REPO_ROOT = ROOT / "repositories" / "pendulum"
    else:
        REPO_ROOT = ROOT / "generation" / "Pendulum"

if not REPO_ROOT.exists():
    pytest.skip(
        "Target repository does not exist: {}".format(REPO_ROOT),
        allow_module_level=True,
    )

src_pkg_init = REPO_ROOT / "src" / PACKAGE_NAME / "__init__.py"
root_pkg_init = REPO_ROOT / PACKAGE_NAME / "__init__.py"

if src_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT / "src"))
elif root_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT))
else:
    pytest.skip(
        "Could not find '{}' package under repo root. Expected {} or {}.".format(
            PACKAGE_NAME, src_pkg_init, root_pkg_init
        ),
        allow_module_level=True,
    )

try:
    import pendulum  # type: ignore  # noqa: E402
except Exception as exc:
    pytest.skip(
        "Failed to import pendulum from {}: {}".format(REPO_ROOT, exc),
        allow_module_level=True,
    )


def _has_attr(obj, name: str) -> bool:
    return getattr(obj, name, None) is not None


# ---------------------------------------------------------------------------
# Existing tests (kept original intent)
# ---------------------------------------------------------------------------

def test_parse_and_timezone_conversion() -> None:
    """Parse an ISO string and convert between timezones."""
    dt_utc = pendulum.parse("2020-01-01T12:00:00+00:00")

    assert dt_utc.year == 2020
    assert dt_utc.month == 1
    assert dt_utc.day == 1

    offset_utc = dt_utc.utcoffset()
    assert offset_utc is not None
    assert offset_utc.total_seconds() == 0

    dt_tokyo = dt_utc.in_timezone("Asia/Tokyo")
    offset_tokyo = dt_tokyo.utcoffset()
    assert offset_tokyo is not None
    assert offset_tokyo.total_seconds() == 9 * 60 * 60

    as_str = dt_tokyo.to_datetime_string()
    assert as_str.startswith("2020-01-01 21:00:00")


def test_datetime_arithmetic_and_duration() -> None:
    """Basic arithmetic with pendulum.datetime and pendulum.duration."""
    base = pendulum.datetime(2021, 3, 15, 10, 30, 0, tz="UTC")

    shifted = base.add(days=2, hours=5, minutes=15)
    delta = shifted - base

    assert delta.days == 2
    assert delta.seconds == 5 * 60 * 60 + 15 * 60

    dur = pendulum.duration(days=3, hours=4)
    via_duration = base + dur
    via_add = base.add(days=3, hours=4)
    assert via_duration == via_add


def test_diff_for_humans_months() -> None:
    """Human-readable differences between two datetimes."""
    start = pendulum.datetime(2011, 8, 1, tz="UTC")
    end = start.add(months=1)

    text = start.diff_for_humans(end)
    assert "month" in text
    assert any(token in text for token in ("1 month", "a month"))


# ---------------------------------------------------------------------------
# Added functional tests (happy-path) - total >= 10 test_* functions
# ---------------------------------------------------------------------------

def test_parse_date_only_to_date_string() -> None:
    """Parse a date-only string and verify normalized date output."""
    d = pendulum.parse("2020-02-29")
    assert d.year == 2020
    assert d.month == 2
    assert d.day == 29
    assert d.to_date_string() == "2020-02-29"


def test_datetime_to_iso8601_string_roundtrip() -> None:
    """Create a datetime and verify ISO8601 string contains expected offset."""
    dt = pendulum.datetime(2020, 1, 1, 12, 0, 0, tz="UTC")
    iso = dt.to_iso8601_string()
    assert "2020-01-01" in iso
    assert "12:00:00" in iso
    assert iso.endswith("Z") or iso.endswith("+00:00")


def test_formatting_with_custom_pattern() -> None:
    """Verify formatting with a custom pattern is stable for a fixed datetime."""
    dt = pendulum.datetime(2021, 12, 31, 23, 59, 58, tz="UTC")
    s = dt.format("YYYY/MM/DD HH:mm:ss")
    assert s == "2021/12/31 23:59:58"


def test_start_of_end_of_day() -> None:
    """Check start_of and end_of for a day boundary."""
    dt = pendulum.datetime(2020, 5, 20, 13, 14, 15, tz="UTC")

    sod = dt.start_of("day")
    eod = dt.end_of("day")

    assert sod.hour == 0 and sod.minute == 0 and sod.second == 0
    assert eod.hour == 23 and eod.minute == 59 and eod.second == 59
    assert sod.to_date_string() == "2020-05-20"
    assert eod.to_date_string() == "2020-05-20"


def test_weekday_and_isoweekday_values() -> None:
    """Validate weekday values for a known date (2020-01-01 is Wednesday)."""
    dt = pendulum.date(2020, 1, 1)
    assert dt.weekday() == 2
    assert dt.isoweekday() == 3


def test_duration_total_seconds_and_components() -> None:
    """Verify duration reports correct total seconds and has component attributes."""
    dur = pendulum.duration(days=1, hours=2, minutes=3, seconds=4)

    # Total seconds is the most stable cross-version contract.
    assert dur.total_seconds() == 1 * 86400 + 2 * 3600 + 3 * 60 + 4

    # Component attributes commonly exist; assert them when present.
    assert dur.days == 1
    if _has_attr(dur, "hours"):
        assert int(dur.hours) == 2
    if _has_attr(dur, "minutes"):
        assert int(dur.minutes) == 3

    # remaining_seconds meaning differs across versions; only require it is within a day.
    if _has_attr(dur, "remaining_seconds"):
        rs = int(dur.remaining_seconds)
        assert 0 <= rs < 86400


def test_interval_range_daily_count_and_endpoints() -> None:
    """Create an interval and verify daily range count and endpoints."""
    if not hasattr(pendulum, "interval"):
        pytest.skip("pendulum.interval is not available in this implementation")

    start = pendulum.date(2020, 1, 1)
    end = pendulum.date(2020, 1, 5)

    iv = pendulum.interval(start, end)
    dates = list(iv.range("days"))

    assert len(dates) == 5
    assert dates[0].to_date_string() == "2020-01-01"
    assert dates[-1].to_date_string() == "2020-01-05"


def test_in_timezone_preserves_instant() -> None:
    """Converting timezones should preserve the instant (timestamp)."""
    dt_utc = pendulum.datetime(2020, 6, 1, 0, 0, 0, tz="UTC")
    dt_ny = dt_utc.in_timezone("America/New_York")

    assert int(dt_utc.timestamp()) == int(dt_ny.timestamp())
    assert dt_ny.to_date_string() in ("2020-05-31", "2020-06-01")


def test_diff_in_days_is_integer() -> None:
    """Compute diff in days between two dates."""
    a = pendulum.date(2020, 1, 1)
    b = pendulum.date(2020, 1, 11)

    diff = b.diff(a)
    days = int(diff.in_days())
    assert days == 10


def test_add_months_across_year_boundary() -> None:
    """Add months and verify year boundary transitions."""
    dt = pendulum.date(2019, 12, 15)
    dt2 = dt.add(months=2)
    assert dt2.year == 2020
    assert dt2.month == 2
    assert dt2.day == 15
