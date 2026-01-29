from datetime import date, timedelta, timezone

import pytest

import astral
from astral.sun import sun, sunrise, sunset, dawn, dusk, noon
from astral.moon import phase

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None


def test_import_surface():
    assert hasattr(astral, "LocationInfo")
    assert hasattr(astral, "AstralError")
    assert callable(sun)
    assert callable(sunrise)
    assert callable(sunset)
    assert callable(phase)


def test_locationinfo_observer_fields():
    loc = astral.LocationInfo(
        name="London",
        region="England",
        timezone="Europe/London",
        latitude=51.5074,
        longitude=-0.1278,
    )
    obs = loc.observer
    assert obs.latitude == pytest.approx(51.5074)
    assert obs.longitude == pytest.approx(-0.1278)
    assert obs.elevation == pytest.approx(0.0)


def test_sun_dict_and_helpers_consistent():
    tz = ZoneInfo("Europe/London") if ZoneInfo else timezone.utc
    loc = astral.LocationInfo(
        name="London",
        region="England",
        timezone="Europe/London",
        latitude=51.5074,
        longitude=-0.1278,
    )
    d = date(2024, 6, 21)
    s = sun(loc.observer, date=d, tzinfo=tz)
    assert set(["dawn", "sunrise", "noon", "sunset", "dusk"]).issubset(s.keys())

    assert sunrise(loc.observer, date=d, tzinfo=tz) == s["sunrise"]
    assert sunset(loc.observer, date=d, tzinfo=tz) == s["sunset"]
    assert noon(loc.observer, date=d, tzinfo=tz) == s["noon"]
    assert dawn(loc.observer, date=d, tzinfo=tz, depression=6) == s["dawn"]
    assert dusk(loc.observer, date=d, tzinfo=tz, depression=6) == s["dusk"]

    # Ordering for a normal mid-latitude summer day
    assert s["dawn"] < s["sunrise"] < s["noon"] < s["sunset"] < s["dusk"]
    assert s["sunrise"].tzinfo is not None


def test_tzinfo_string_supported_and_awareness():
    if not ZoneInfo:
        pytest.skip("zoneinfo not available")
    loc = astral.LocationInfo(
        name="New York",
        region="USA",
        timezone="America/New_York",
        latitude=40.7128,
        longitude=-74.0060,
    )
    d = date(2024, 3, 10)  # DST transition day in US
    s = sun(loc.observer, date=d, tzinfo="America/New_York")
    assert s["noon"].tzinfo is not None
    assert s["noon"].utcoffset() is not None


def test_polar_night_raises():
    if not ZoneInfo:
        tz = timezone.utc
    else:
        tz = ZoneInfo("Europe/Oslo")
    # Tromsø
    loc = astral.LocationInfo(
        name="Tromso",
        region="Norway",
        timezone="Europe/Oslo",
        latitude=69.6492,
        longitude=18.9553,
    )
    d = date(2024, 12, 21)
    with pytest.raises((astral.SunNeverRisesError, astral.AstralError, ValueError)):
        sunrise(loc.observer, date=d, tzinfo=tz)


def test_moon_phase_range_and_monotonicish():
    start = date(2025, 1, 1)
    vals = [phase(start + timedelta(days=i)) for i in range(40)]
    assert all(0.0 <= v < 29.53058867 for v in vals)

    # Ensure no wild backwards jumps except wrap-around at new moon
    wraps = 0
    for a, b in zip(vals, vals[1:]):
        if b < a:
            wraps += 1
            # wrap should go close to 0
            assert b < 3.0
            assert a > 26.0
        else:
            # typical increment roughly ~1 day
            assert (b - a) < 2.0
    assert wraps <= 2