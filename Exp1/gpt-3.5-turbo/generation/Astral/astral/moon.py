"""
Moon phase calculation compatible with Astral core API.
"""

from datetime import date as Date
from math import floor

def phase(date: Date) -> float:
    """
    Calculate the moon phase for the given date.
    Returns a float between 0 and 29.53 (synodic month length).
    0 = New Moon, 14.77 = Full Moon, 29.53 = New Moon again.
    """
    # Algorithm from Astronomical Algorithms by Jean Meeus (simplified)
    # Known new moon reference: 2000 Jan 6 at 18:14 UTC (Julian day 2451550.1)
    # Synodic month length = 29.53058867 days

    if not hasattr(date, "year"):
        raise TypeError("date must be a date or datetime object")

    year = date.year
    month = date.month
    day = date.day

    if month < 3:
        year -= 1
        month += 12

    K = floor((year + (month - 1) / 12 - 2000) * 12.3685)

    # Time in Julian centuries from 2000 Jan 0.5
    T = K / 1236.85

    # Mean new moon
    Jd1 = 2451550.09766 + 29.530588861 * K \
          + 0.00015437 * T * T - 0.000000150 * T * T * T + 0.00000000073 * T * T * T * T

    # Sun's mean anomaly
    M = 2.5534 + 29.10535670 * K - 0.0000014 * T * T - 0.00000011 * T * T * T

    # Moon's mean anomaly
    Mprime = 201.5643 + 385.81693528 * K + 0.0107582 * T * T + 0.00001238 * T * T * T - 0.000000058 * T * T * T * T

    # Moon's argument of latitude
    F = 160.7108 + 390.67050274 * K - 0.0016118 * T * T - 0.00000227 * T * T * T + 0.000000011 * T * T * T * T

    # Normalize angles to [0,360)
    def norm_angle(a):
        return a % 360

    M = norm_angle(M)
    Mprime = norm_angle(Mprime)
    F = norm_angle(F)

    # Age of the moon in days
    # Calculate difference between given date and Jd1
    # Convert input date to Julian day
    def to_julian_day(y, m, d):
        if m <= 2:
            y -= 1
            m += 12
        A = int(y / 100)
        B = 2 - A + int(A / 4)
        JD = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5
        return JD

    JD = to_julian_day(year, month, day)

    age = (JD - Jd1) % 29.53058867

    return age