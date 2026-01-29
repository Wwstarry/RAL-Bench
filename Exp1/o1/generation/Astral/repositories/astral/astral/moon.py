"""
Moon phase calculation compatible with the reference Astral interface.
"""

import datetime
import math

def phase(date=None):
    """
    Return the lunar phase as a floating-point number in a range
    roughly 0..29.53 (the length of the synodic month).
    0 = new moon, ~14.765 = full moon, etc.
    """
    if date is None:
        date = datetime.date.today()

    # Convert input to a date if necessary
    if isinstance(date, datetime.datetime):
        date = date.date()

    # Astral's typical reference date is close to the new moon of 2000-01-06 18:14 UTC
    # We'll define a near epoch:
    # This epoch is 2000-01-06 18:14:00 UTC = JD ~ 2451550.1
    # Synodic month ~ 29.530588853
    # Approach from common new moon reference.

    # Convert date to a float of days since 2000-01-06
    epoch = datetime.date(2000, 1, 6)
    days_since = (date - epoch).days

    # We'll not worry about hours/minutes offset for simpler approach
    # One approach is mod 29.530588853
    synodic_month = 29.530588853
    phase_float = days_since % synodic_month

    # Return the approximate phase
    return phase_float