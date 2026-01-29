import datetime
from enum import IntEnum

# Frequency constants
class FREQ(IntEnum):
    YEARLY = 0
    MONTHLY = 1
    WEEKLY = 2
    DAILY = 3
    HOURLY = 4
    MINUTELY = 5
    SECONDLY = 6

# Weekday constants
class weekday(IntEnum):
    MO = 0
    TU = 1
    WE = 2
    TH = 3
    FR = 4
    SA = 5
    SU = 6

# Alias constants
YEARLY = FREQ.YEARLY
MONTHLY = FREQ.MONTHLY
WEEKLY = FREQ.WEEKLY
DAILY = FREQ.DAILY
HOURLY = FREQ.HOURLY
MINUTELY = FREQ.MINUTELY
SECONDLY = FREQ.SECONDLY

MO, TU, WE, TH, FR, SA, SU = weekday.MO, weekday.TU, weekday.WE, weekday.TH, weekday.FR, weekday.SA, weekday.SU

def rrule(freq, dtstart, interval=1, count=None, until=None, byweekday=None):
    current = dtstart
    results = []
    iterations = 0
    
    while True:
        if count is not None and iterations >= count:
            break
        if until is not None and current > until:
            break
            
        # Apply weekday filter
        if byweekday is not None:
            if current.weekday() in byweekday:
                results.append(current)
        else:
            results.append(current)
        
        # Increment based on frequency
        if freq == DAILY:
            current += datetime.timedelta(days=interval)
        elif freq == WEEKLY:
            current += datetime.timedelta(weeks=interval)
        elif freq == MONTHLY:
            # Simplified month increment
            month = current.month + interval
            year = current.year
            if month > 12:
                year += month // 12
                month = month % 12
            current = current.replace(year=year, month=month)
        elif freq == YEARLY:
            current = current.replace(year=current.year + interval)
        
        iterations += 1
    
    return results