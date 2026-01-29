import datetime as dt

import pytest

import pendulum


def test_facade_imports():
    assert hasattr(pendulum, "datetime")
    assert hasattr(pendulum, "parse")
    assert hasattr(pendulum, "timezone")
    assert hasattr(pendulum, "duration")
    assert pendulum.DateTime is not None
    assert pendulum.Duration is not None


def test_timezone_factory_utc_and_offsets():
    assert pendulum.timezone("UTC") is dt.timezone.utc
    assert pendulum.timezone("Z") is dt.timezone.utc

    tz = pendulum.timezone("+02:00")
    assert tz.utcoffset(None) == dt.timedelta(hours=2)

    tz2 = pendulum.timezone("-0530")
    assert tz2.utcoffset(None) == dt.timedelta(hours=-5, minutes=-30)

    tz3 = pendulum.timezone("+05")
    assert tz3.utcoffset(None) == dt.timedelta(hours=5)


def test_datetime_construction_and_in_timezone():
    d = pendulum.datetime(2020, 1, 1, 0, 0, 0, tz="UTC")
    assert isinstance(d, pendulum.DateTime)
    assert d.tzinfo is dt.timezone.utc

    d2 = d.in_timezone("+02:00")
    assert d2.hour == 2
    assert d2.utcoffset() == dt.timedelta(hours=2)

    naive = pendulum.datetime(2020, 1, 1, 12, 0, 0)
    converted = naive.in_timezone("UTC")
    # deterministic: attaches tz without shifting
    assert converted.hour == 12
    assert converted.tzinfo is dt.timezone.utc


def test_parse_iso8601_variants():
    d = pendulum.parse("2020-01-01")
    assert d.tzinfo is None
    assert (d.year, d.month, d.day, d.hour, d.minute, d.second) == (2020, 1, 1, 0, 0, 0)

    d = pendulum.parse("2020-01-01T10:20:30Z")
    assert d.tzinfo is dt.timezone.utc
    assert (d.hour, d.minute, d.second) == (10, 20, 30)

    d = pendulum.parse("2020-01-01T10:20:30+02:00")
    assert d.utcoffset() == dt.timedelta(hours=2)

    d = pendulum.parse("2020-01-01 10:20")
    assert (d.hour, d.minute, d.second) == (10, 20, 0)

    # attach tz if no tzinfo in string
    d = pendulum.parse("2020-01-01T10:20:30", tz="UTC")
    assert d.tzinfo is dt.timezone.utc
    assert d.hour == 10

    # convert instant if tzinfo exists in string
    d = pendulum.parse("2020-01-01T10:20:30Z", tz="+02:00")
    assert d.hour == 12
    assert d.utcoffset() == dt.timedelta(hours=2)


def test_add_month_clamp_and_year_clamp():
    d = pendulum.datetime(2021, 1, 31)
    d2 = d.add(months=1)
    assert (d2.year, d2.month, d2.day) == (2021, 2, 28)

    d = pendulum.datetime(2020, 2, 29)
    d2 = d.add(years=1)
    assert (d2.year, d2.month, d2.day) == (2021, 2, 28)


def test_subtraction_returns_duration_and_timedelta_equivalent():
    a = pendulum.datetime(2020, 1, 1, tz="UTC")
    b = pendulum.datetime(2020, 1, 2, 3, 4, 5, tz="UTC")
    diff = b - a
    assert isinstance(diff, pendulum.Duration)
    assert diff.as_timedelta() == dt.timedelta(days=1, hours=3, minutes=4, seconds=5)

    back = b - pendulum.duration(days=1)
    assert isinstance(back, pendulum.DateTime)
    assert back == pendulum.datetime(2020, 1, 1, 3, 4, 5, tz="UTC")


def test_diff_for_humans_phrases():
    base = pendulum.datetime(2020, 1, 1, 0, 0, 0, tz="UTC")
    future = base.add(seconds=10)
    past = base.add(seconds=-10)

    assert future.diff_for_humans(base) == "in a few seconds"
    assert past.diff_for_humans(base) == "a few seconds ago"

    future = base.add(seconds=60)
    assert future.diff_for_humans(base) == "in a minute"

    past = base.add(hours=-2)
    assert past.diff_for_humans(base) == "2 hours ago"

    assert past.diff_for_humans(base, absolute=True) == "2 hours"
    assert past.diff_for_humans(base, suffix=False) == "2 hours"