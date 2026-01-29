import datetime as _dt

def diff_for_humans(dt, other=None, absolute=False, locale=None):
    """
    Get a human-readable string representing the difference between two datetimes.
    """
    now = other
    is_now = False
    
    if now is None:
        # Avoid circular import
        from .datetime import DateTime
        now = DateTime.now(dt.tzinfo)
        is_now = True

    diff = dt - now
    total_seconds = diff.total_seconds()
    
    past = total_seconds < 0
    seconds = abs(int(total_seconds))

    if seconds < 1:
        count = 0
        unit = "second"
    elif seconds < 45:
        count = seconds
        unit = "second"
    elif seconds < 90:
        count = 1
        unit = "minute"
    elif seconds < 45 * 60:
        count = round(seconds / 60)
        unit = "minute"
    elif seconds < 90 * 60:
        count = 1
        unit = "hour"
    elif seconds < 22 * 3600:
        count = round(seconds / 3600)
        unit = "hour"
    elif seconds < 36 * 3600:
        count = 1
        unit = "day"
    elif seconds < 25 * 86400:
        count = round(seconds / 86400)
        unit = "day"
    elif seconds < 45 * 86400:
        count = 1
        unit = "month"
    elif seconds < 345 * 86400:
        count = round(seconds / (30 * 86400)) # Approx
        unit = "month"
    else:
        count = round(seconds / (365 * 86400)) # Approx
        unit = "year"

    if count == 0 and unit == "second":
        return "just now"

    s = "s" if count != 1 else ""
    text = f"{count} {unit}{s}"

    if absolute:
        return text

    if past:
        return f"{text} ago"
    else:
        return f"in {text}"

def to_iso8601_string(dt):
    """
    Return ISO 8601 string.
    """
    return dt.isoformat()