# astral/moon.py

from datetime import date

def phase(date_: date) -> float:
    """
    Return the moon phase for the given date.
    0 = new moon, 14.77 = full moon, 29.53 = next new moon
    Returns value in [0, 29.53).
    Algorithm is a simplified version of John Conway's method.
    """
    # Reference new moon: 2000-01-06 18:14 UTC (Julian date 2451550.1)
    # Synodic month (new moon to new moon): 29.53058867 days
    y = date_.year
    m = date_.month
    d = date_.day
    if m < 3:
        y -= 1
        m += 12
    k1 = int(365.25 * (y + 4712))
    k2 = int(30.6 * (m + 1))
    k3 = int(((y / 100) + 49) * 0.75) - 38
    jd = k1 + k2 + d + 59  # Julian day at noon
    jd -= k3
    # Days since known new moon
    days = jd - 2451550.1
    # Normalize to [0, 29.53)
    lunations = days / 29.53058867
    phase = (lunations - int(lunations)) * 29.53058867
    if phase < 0:
        phase += 29.53058867
    return phase