"""
Formatting utilities for human-readable output.
"""


def diff_for_humans(dt1, dt2, absolute=False):
    """
    Get a human-readable difference between two datetimes.
    
    Args:
        dt1: First datetime
        dt2: Second datetime
        absolute: Whether to omit the relative part (ago/from now)
    
    Returns:
        str: Human-readable difference
    """
    delta = dt1 - dt2
    total_seconds = delta.total_seconds()
    
    # Determine if it's in the past or future
    is_past = total_seconds < 0
    total_seconds = abs(total_seconds)
    
    # Calculate time units
    years = int(total_seconds / (365.25 * 24 * 3600))
    if years > 0:
        total_seconds -= years * 365.25 * 24 * 3600
    
    months = int(total_seconds / (30.44 * 24 * 3600))
    if months > 0:
        total_seconds -= months * 30.44 * 24 * 3600
    
    weeks = int(total_seconds / (7 * 24 * 3600))
    if weeks > 0:
        total_seconds -= weeks * 7 * 24 * 3600
    
    days = int(total_seconds / (24 * 3600))
    if days > 0:
        total_seconds -= days * 24 * 3600
    
    hours = int(total_seconds / 3600)
    if hours > 0:
        total_seconds -= hours * 3600
    
    minutes = int(total_seconds / 60)
    if minutes > 0:
        total_seconds -= minutes * 60
    
    seconds = int(total_seconds)
    
    # Build the human-readable string
    if years > 0:
        unit = "year" if years == 1 else "years"
        value = years
    elif months > 0:
        unit = "month" if months == 1 else "months"
        value = months
    elif weeks > 0:
        unit = "week" if weeks == 1 else "weeks"
        value = weeks
    elif days > 0:
        unit = "day" if days == 1 else "days"
        value = days
    elif hours > 0:
        unit = "hour" if hours == 1 else "hours"
        value = hours
    elif minutes > 0:
        unit = "minute" if minutes == 1 else "minutes"
        value = minutes
    else:
        unit = "second" if seconds == 1 else "seconds"
        value = seconds if seconds > 0 else 0
    
    result = f"{value} {unit}"
    
    if not absolute:
        if is_past:
            result += " ago"
        else:
            result = "in " + result
    
    return result