import pendulum
import pytest


def test_zoneinfo_paris_if_available():
    try:
        tz = pendulum.timezone("Europe/Paris")
    except ValueError:
        pytest.skip("ZoneInfo/tzdata not available for Europe/Paris in environment")
    assert tz is not None
    # basic sanity: tzname exists for some datetime
    d = pendulum.datetime(2020, 1, 1, tz="UTC").in_timezone(tz)
    assert d.tzinfo is not None