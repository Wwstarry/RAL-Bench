"""
A grab-bag of small math helpers used by the sun/moon calculations.
All angles are in **degrees** unless otherwise specified.
"""
from __future__ import annotations

import math

__all__ = [
    "to_range",
    "sin_deg",
    "cos_deg",
    "tan_deg",
    "asin_deg",
    "acos_deg",
    "atan_deg",
    "day_of_year",
    "julian_day",
]


def to_range(x: float, minimum: float, maximum: float) -> float:
    """Wrap *x* so that *minimum* <= x < *maximum* (like modulo)."""
    span = maximum - minimum
    while x < minimum:
        x += span
    while x >= maximum:
        x -= span
    return x


def sin_deg(d: float) -> float:
    return math.sin(math.radians(d))


def cos_deg(d: float) -> float:
    return math.cos(math.radians(d))


def tan_deg(d: float) -> float:
    return math.tan(math.radians(d))


def asin_deg(x: float) -> float:
    return math.degrees(math.asin(x))


def acos_deg(x: float) -> float:
    return math.degrees(math.acos(x))


def atan_deg(x: float) -> float:
    return math.degrees(math.atan(x))


# ---------------------------------------------------------------------- #
# Date/Time helpers
# ---------------------------------------------------------------------- #
def day_of_year(date) -> int:
    """Return the day of year (1-366) for *date* (datetime.date)."""
    return date.timetuple().tm_yday


def julian_day(date) -> float:
    """
    Return the Julian Day Number at 12:00 UTC for the given *date*.

    The algorithm is valid for Gregorian dates after 1582-10-15 which is
    well within our needs for contemporary calculations.
    """
    y = date.year
    m = date.month
    d = date.day

    if m <= 2:
        y -= 1
        m += 12

    a = y // 100
    b = 2 - a + a // 4

    jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5
    return jd