import datetime
import math

def phase(date=None):
    """
    Calculate the phase of the moon.
    
    Returns a number between 0 and 29.53...
    0 = New Moon
    7.38 = First Quarter
    14.76 = Full Moon
    22.15 = Last Quarter
    """
    if date is None:
        date = datetime.date.today()
        
    # Epoch: 2000-01-06 18:14 UTC (New Moon)
    # JD = 2451550.1
    epoch = 2451550.1
    
    # Calculate JD for the given date (at noon? Astral usually takes date)
    # Let's use noon to be safe or 00:00?
    # If date is just a date object, treat as 00:00 or Noon?
    # Astral docs say: "Calculates the phase of the moon on the specified date."
    # Usually this implies the phase at a specific time or average.
    # Let's use 00:00 UTC.
    
    y = date.year
    m = date.month
    d = date.day
    if m <= 2:
        y -= 1
        m += 12
    a = math.floor(y / 100)
    b = 2 - a + math.floor(a / 4)
    jd = math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + b - 1524.5
    
    # Synodic month
    synodic = 29.530588853
    
    # Days since epoch
    days = jd - epoch
    
    # Phase
    # Normalize to 0..synodic
    p = days % synodic
    if p < 0:
        p += synodic
        
    return p