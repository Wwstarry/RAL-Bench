"""
Moon phase calculations.
"""

import math
from datetime import datetime


def _julian_day(date: datetime) -> float:
    """Calculate Julian Day Number."""
    a = (14 - date.month) // 12
    y = date.year + 4800 - a
    m = date.month + 12 * a - 3
    jdn = date.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    return jdn + (date.hour - 12) / 24.0 + date.minute / 1440.0 + date.second / 86400.0


def phase(date: datetime) -> float:
    """
    Calculate the lunar phase for a given date.
    
    Args:
        date: Date to calculate lunar phase for
    
    Returns:
        Lunar phase as a float between 0 and 1, where:
        0 = New Moon
        0.25 = First Quarter
        0.5 = Full Moon
        0.75 = Last Quarter
    """
    # Reference new moon: January 6, 2000, 18:14 UTC
    known_new_moon = datetime(2000, 1, 6, 18, 14, 0)
    known_new_moon_jd = _julian_day(known_new_moon)
    
    # Lunar cycle in days (synodic month)
    lunar_cycle = 29.530588861
    
    # Calculate Julian Day for the given date
    jd = _julian_day(date)
    
    # Calculate days since known new moon
    days_since = jd - known_new_moon_jd
    
    # Calculate phase (0 to 1)
    phase_value = (days_since % lunar_cycle) / lunar_cycle
    
    # Ensure phase is in valid range
    phase_value = phase_value % 1.0
    
    return phase_value