from datetime import timedelta, datetime
import time

def precisedelta(delta, minimum_unit='seconds', format='%0.2f'):
    """Format a timedelta into a human-readable string with precision control."""
    if not isinstance(delta, timedelta):
        raise TypeError("precisedelta() argument must be a timedelta")

    units = {
        'days': delta.days,
        'hours': delta.seconds // 3600,
        'minutes': (delta.seconds % 3600) // 60,
        'seconds': delta.seconds % 60,
        'microseconds': delta.microseconds
    }

    unit_order = ['days', 'hours', 'minutes', 'seconds', 'microseconds']
    start_idx = unit_order.index(minimum_unit)
    
    parts = []
    for unit in unit_order[start_idx:]:
        value = units[unit]
        if value > 0 or (unit == minimum_unit and not parts):
            if unit == 'microseconds':
                parts.append(f"{format % (value / 1000000)} seconds")
            else:
                parts.append(f"{value} {unit}")
    
    return ' '.join(parts)

def naturaldelta(value, months=True):
    """Convert a timedelta or seconds into a human-readable delta."""
    if isinstance(value, timedelta):
        seconds = value.total_seconds()
    elif isinstance(value, (int, float)):
        seconds = value
    else:
        raise TypeError("naturaldelta() argument must be timedelta, int, or float")
    
    if seconds < 60:
        return f"{int(seconds)} seconds"
    minutes = seconds / 60
    if minutes < 60:
        return f"{int(minutes)} minutes"
    hours = minutes / 60
    if hours < 24:
        return f"{int(hours)} hours"
    days = hours / 24
    if days < 30 or not months:
        return f"{int(days)} days"
    months = days / 30
    if months < 12:
        return f"{int(months)} months"
    years = days / 365
    return f"{int(years)} years"

def naturaltime(value, future=False, months=True):
    """Convert a datetime or timedelta into a human-readable relative time."""
    now = datetime.now()
    if isinstance(value, timedelta):
        delta = value
    elif isinstance(value, datetime):
        delta = now - value
    else:
        raise TypeError("naturaltime() argument must be timedelta or datetime")
    
    delta_abs = abs(delta)
    humanized = naturaldelta(delta_abs, months)
    
    if future:
        return f"in {humanized}"
    elif delta.total_seconds() < 0:
        return f"{humanized} from now"
    else:
        return f"{humanized} ago"