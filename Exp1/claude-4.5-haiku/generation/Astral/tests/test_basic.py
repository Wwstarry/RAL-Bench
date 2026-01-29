"""Basic tests for astral functionality."""

import pytest
from datetime import datetime
import pytz
from astral import LocationInfo
from astral.sun import sun, sunrise, sunset
from astral.moon import phase


def test_location_info_creation():
    """Test LocationInfo creation."""
    loc = LocationInfo("London", "England", 51.5074, -0.1278, "Europe/London")
    assert loc.name == "London"
    assert loc.latitude == 51.5074
    assert loc.longitude == -0.1278
    assert loc.timezone == "Europe/London"


def test_observer_property():
    """Test observer property on LocationInfo."""
    loc = LocationInfo("London", "England", 51.5074, -0.1278, "Europe/London")
    obs = loc.observer
    assert obs.latitude == 51.5074
    assert obs.longitude == -0.1278
    assert obs.elevation == 0.0


def test_sun_times():
    """Test sun time calculations."""
    loc = LocationInfo("London", "England", 51.5074, -0.1278, "Europe/London")
    date = datetime(2023, 6, 21)
    
    times = sun(loc.observer, date, loc.tzinfo())
    
    assert 'dawn' in times
    assert 'sunrise' in times
    assert 'noon' in times
    assert 'sunset' in times
    assert 'dusk' in times
    
    # Check that times are in order
    assert times['dawn'] < times['sunrise']
    assert times['sunrise'] < times['noon']
    assert times['noon'] < times['sunset']
    assert times['sunset'] < times['dusk']


def test_sunrise_function():
    """Test sunrise helper function."""
    loc = LocationInfo("London", "England", 51.5074, -0.1278, "Europe/London")
    date = datetime(2023, 6, 21)
    
    sr = sunrise(loc.observer, date, loc.tzinfo())
    times = sun(loc.observer, date, loc.tzinfo())
    
    # Should match the sunrise from sun()
    assert sr == times['sunrise']


def test_sunset_function():
    """Test sunset helper function."""
    loc = LocationInfo("London", "England", 51.5074, -0.1278, "Europe/London")
    date = datetime(2023, 6, 21)
    
    ss = sunset(loc.observer, date, loc.tzinfo())
    times = sun(loc.observer, date, loc.tzinfo())
    
    # Should match the sunset from sun()
    assert ss == times['sunset']


def test_moon_phase():
    """Test moon phase calculation."""
    # Test a few known dates
    phase_value = phase(datetime(2023, 1, 1))
    
    # Phase should be between 0 and 1
    assert 0 <= phase_value <= 1


def test_moon_phase_monotonic():
    """Test that moon phase is monotonic across consecutive days."""
    phases = []
    for day in range(1, 30):
        p = phase(datetime(2023, 1, day))
        phases.append(p)
    
    # Check that phases are generally increasing (allowing for wrap-around)
    for i in range(len(phases) - 1):
        # Either increasing or wrapped around
        assert phases[i+1] >= phases[i] or phases[i+1] < 0.1


def test_timezone_aware_output():
    """Test that returned times are timezone-aware."""
    loc = LocationInfo("London", "England", 51.5074, -0.1278, "Europe/London")
    date = datetime(2023, 6, 21)
    
    times = sun(loc.observer, date, loc.tzinfo())
    
    for key, dt in times.items():
        assert dt.tzinfo is not None


def test_different_timezones():
    """Test sun times in different timezones."""
    loc = LocationInfo("London", "England", 51.5074, -0.1278, "Europe/London")
    date = datetime(2023, 6, 21)
    
    london_tz = pytz.timezone("Europe/London")
    utc_tz = pytz.UTC
    
    times_london = sun(loc.observer, date, london_tz)
    times_utc = sun(loc.observer, date, utc_tz)
    
    # Same moment in time, different timezone representations
    assert times_london['sunrise'].astimezone(utc_tz) == times_utc['sunrise']