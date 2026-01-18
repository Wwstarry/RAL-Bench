from __future__ import annotations

import datetime as dt
import os
import sys
from pathlib import Path

import pytest

# Root directory of the benchmark project
ROOT = Path(__file__).resolve().parents[2]

# Decide whether to test the reference repository or the generated one.
target = os.environ.get("DATEUTIL_TARGET", "reference").lower()
if target == "reference":
    # The source package lives under src/dateutil in the reference repo.
    REPO_ROOT = ROOT / "repositories" / "dateutil" / "src"
else:
    # For generated code we assume the "dateutil" package is directly under generation/Dateutil.
    REPO_ROOT = ROOT / "generation" / "Dateutil"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dateutil import parser, tz  # type: ignore  # noqa: E402
from dateutil.relativedelta import relativedelta  # type: ignore  # noqa: E402
from dateutil.rrule import (  # type: ignore  # noqa: E402
    rrule,
    WEEKLY,
    DAILY,
    MONTHLY,
    MO,
    TU,
    WE,
    FR,
)


def test_parser_basic_iso_and_natural_language() -> None:
    """dateutil.parser.parse should handle ISO and natural-ish formats."""
    d1 = parser.parse("2020-05-17T13:45:00Z")
    d2 = parser.parse("May 17, 2020 1:45 pm UTC")

    # Both should be timezone-aware and equal.
    assert d1.tzinfo is not None
    assert d2.tzinfo is not None
    assert d1 == d2

    # Parsing a date-only string should produce a datetime at midnight.
    d3 = parser.parse("2020-05-17")
    assert d3.time() == dt.time(0, 0, 0)


def test_parser_invalid_string_raises() -> None:
    """Parsing a clearly invalid string should raise a normal exception."""
    with pytest.raises(Exception):
        _ = parser.parse("this is not a date at all")


def test_parser_dayfirst_changes_interpretation() -> None:
    """dayfirst should affect ambiguous numeric dates."""
    # 01/02/2020 is ambiguous: could be Jan 2 or Feb 1.
    d_dayfirst = parser.parse("01/02/2020", dayfirst=True)
    d_monthfirst = parser.parse("01/02/2020", dayfirst=False)

    assert d_dayfirst.date() != d_monthfirst.date()
    assert d_dayfirst.date() == dt.date(2020, 2, 1)
    assert d_monthfirst.date() == dt.date(2020, 1, 2)


def test_parser_with_default_fills_missing_fields() -> None:
    """default= should fill missing fields when parsing partial dates."""
    default = dt.datetime(2020, 1, 1, 12, 34, 56)
    parsed = parser.parse("March 5", default=default)

    assert parsed.year == 2020
    assert parsed.month == 3
    assert parsed.day == 5
    # Missing time should come from default
    assert parsed.hour == 12
    assert parsed.minute == 34
    assert parsed.second == 56


def test_parser_fuzzy_ignores_noise() -> None:
    """fuzzy=True should ignore extra words around a valid date token."""
    parsed = parser.parse("Noise before 2020-12-31 noise after", fuzzy=True)
    assert parsed.date() == dt.date(2020, 12, 31)


def test_parser_tzinfos_mapping_for_abbrev() -> None:
    """tzinfos should allow parsing known abbreviations deterministically."""
    pst = tz.tzoffset("PST", -8 * 3600)
    parsed = parser.parse("2020-01-01 10:00 PST", tzinfos={"PST": pst})

    assert parsed.tzinfo is not None
    assert parsed.utcoffset() == dt.timedelta(hours=-8)
    # 10:00 PST == 18:00 UTC
    as_utc = parsed.astimezone(tz.UTC)
    assert as_utc.hour == 18
    assert as_utc.minute == 0


def test_relativedelta_arithmetic_and_fields() -> None:
    """relativedelta should support calendar arithmetic and field inspection."""
    start = dt.date(2020, 1, 31)

    # One month later should be the last day of February 2020 (29, leap year).
    end = start + relativedelta(months=+1)
    assert end == dt.date(2020, 2, 29)

    # Difference between two dates should expose year/month/day fields.
    delta = relativedelta(dt.date(2021, 3, 15), dt.date(2020, 1, 10))
    assert isinstance(delta.years, int)
    assert isinstance(delta.months, int)
    assert isinstance(delta.days, int)


def test_relativedelta_leap_day_rolls_to_feb_28() -> None:
    """Feb 29 + 1 year should land on Feb 28 in a non-leap year."""
    start = dt.date(2020, 2, 29)
    end = start + relativedelta(years=+1)
    assert end == dt.date(2021, 2, 28)


def test_relativedelta_weekday_next_monday() -> None:
    """weekday=MO(+1) should move to the next Monday."""
    # 2020-01-01 is Wednesday.
    start = dt.date(2020, 1, 1)
    next_monday = start + relativedelta(weekday=MO(+1))
    assert next_monday == dt.date(2020, 1, 6)
    assert next_monday.weekday() == 0  # Monday


def test_rrule_weekly_recurrence_with_byweekday() -> None:
    """rrule should generate weekly recurrences matching a weekday pattern."""
    start = dt.datetime(2020, 1, 1, 9, 0, 0, tzinfo=tz.UTC)

    # Every week on Monday, Wednesday and Friday at 09:00 UTC.
    rule = rrule(
        WEEKLY,
        dtstart=start,
        byweekday=(MO, WE, FR),
        count=6,
    )

    events = list(rule)
    assert len(events) == 6

    weekdays = [ev.weekday() for ev in events]
    assert set(weekdays).issubset({0, 2, 4})

    for prev, curr in zip(events, events[1:]):
        assert curr > prev
        assert curr.hour == 9
        assert curr.tzinfo is not None


def test_rrule_daily_interval_and_count() -> None:
    """DAILY with interval should step correctly."""
    start = dt.datetime(2020, 1, 1, 0, 0, 0, tzinfo=tz.UTC)
    rule = rrule(DAILY, dtstart=start, interval=2, count=4)
    events = list(rule)

    assert len(events) == 4
    assert events[0] == start
    assert events[1] == start + dt.timedelta(days=2)
    assert events[2] == start + dt.timedelta(days=4)
    assert events[3] == start + dt.timedelta(days=6)


def test_rrule_monthly_bymonthday_15() -> None:
    """MONTHLY bymonthday should hit the requested day-of-month."""
    start = dt.datetime(2020, 1, 1, 9, 0, 0, tzinfo=tz.UTC)
    rule = rrule(MONTHLY, dtstart=start, bymonthday=15, count=3)
    events = list(rule)

    assert len(events) == 3
    assert all(ev.day == 15 for ev in events)
    assert all(ev.hour == 9 for ev in events)


def test_tz_conversion_between_timezones() -> None:
    """Fixed-offset time zones should support converting between offsets."""
    ny = tz.tzoffset("NY", -5 * 3600)  # UTC-5
    london = tz.tzoffset("LDN", 0)  # UTC

    naive = dt.datetime(2020, 3, 8, 1, 30, 0)  # around DST change in US
    ny_local = naive.replace(tzinfo=ny)

    london_time = ny_local.astimezone(london)
    ny_roundtrip = london_time.astimezone(ny)

    assert abs((ny_roundtrip - ny_local).total_seconds()) < 1.0


def test_tz_offset_roundtrip_from_explicit_offset_string() -> None:
    """Parsing explicit offsets should allow stable conversion to UTC."""
    d = parser.parse("2020-01-01T00:00:00+09:00")
    assert d.tzinfo is not None

    utc_d = d.astimezone(tz.UTC)
    assert utc_d.hour == 15  # 00:00 JST == 15:00 UTC previous day
    assert utc_d.minute == 0
