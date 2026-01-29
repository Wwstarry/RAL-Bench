"""
Time humanization functions.
"""

from datetime import datetime, timedelta, timezone
import math


def naturaldelta(value, months=True, minimum_unit="seconds"):
    """
    Return a natural representation of a timedelta or number of seconds.
    
    Args:
        value: timedelta or number of seconds
        months: Whether to use months in output
        minimum_unit: Minimum unit to display
        
    Returns:
        String like "2 hours", "3 days", etc.
    """
    if isinstance(value, timedelta):
        seconds = value.total_seconds()
    else:
        try:
            seconds = float(value)
        except (ValueError, TypeError):
            return str(value)
    
    abs_seconds = abs(seconds)
    
    # Define time units
    years = abs_seconds / (365.25 * 24 * 3600)
    months_val = abs_seconds / (30.44 * 24 * 3600)
    days = abs_seconds / (24 * 3600)
    hours = abs_seconds / 3600
    minutes = abs_seconds / 60
    
    if minimum_unit == "seconds":
        min_seconds = 1
    elif minimum_unit == "minutes":
        min_seconds = 60
    elif minimum_unit == "hours":
        min_seconds = 3600
    elif minimum_unit == "days":
        min_seconds = 86400
    else:
        min_seconds = 1
    
    if abs_seconds < min_seconds:
        if minimum_unit == "minutes":
            return "a minute"
        elif minimum_unit == "hours":
            return "an hour"
        elif minimum_unit == "days":
            return "a day"
        else:
            return "a moment"
    
    if years >= 1:
        years_int = int(round(years))
        if years_int == 1:
            return "a year"
        return "%d years" % years_int
    
    if months and months_val >= 1:
        months_int = int(round(months_val))
        if months_int == 1:
            return "a month"
        return "%d months" % months_int
    
    if days >= 1:
        days_int = int(round(days))
        if days_int == 1:
            return "a day"
        return "%d days" % days_int
    
    if hours >= 1:
        hours_int = int(round(hours))
        if hours_int == 1:
            return "an hour"
        return "%d hours" % hours_int
    
    if minutes >= 1:
        minutes_int = int(round(minutes))
        if minutes_int == 1:
            return "a minute"
        return "%d minutes" % minutes_int
    
    seconds_int = int(round(abs_seconds))
    if seconds_int == 1:
        return "a second"
    return "%d seconds" % seconds_int


def naturaltime(value, future=False, months=True, minimum_unit="seconds", when=None):
    """
    Return a natural representation of a time relative to now.
    
    Args:
        value: datetime or timedelta
        future: Whether the time is in the future
        months: Whether to use months
        minimum_unit: Minimum unit to display
        when: Reference time (defaults to now)
        
    Returns:
        String like "2 hours ago", "in 3 days", etc.
    """
    if when is None:
        now = datetime.now(timezone.utc)
    else:
        now = when
    
    if isinstance(value, timedelta):
        delta = value
    elif isinstance(value, datetime):
        # Make both timezone-aware or both naive
        if value.tzinfo is None and now.tzinfo is not None:
            value = value.replace(tzinfo=timezone.utc)
        elif value.tzinfo is not None and now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        delta = value - now
    else:
        try:
            delta = timedelta(seconds=float(value))
        except (ValueError, TypeError):
            return str(value)
    
    seconds = delta.total_seconds()
    
    if abs(seconds) < 1:
        return "now"
    
    natural = naturaldelta(delta, months=months, minimum_unit=minimum_unit)
    
    if seconds < 0:
        return natural + " ago"
    else:
        return "in " + natural


def naturalday(value, format='%b %d', when=None):
    """
    Return a natural day representation.
    
    Args:
        value: datetime object
        format: Format string for dates not today/yesterday/tomorrow
        when: Reference time (defaults to now)
        
    Returns:
        String like "today", "yesterday", "tomorrow", or formatted date
    """
    if when is None:
        now = datetime.now()
    else:
        now = when
    
    if not isinstance(value, datetime):
        return str(value)
    
    # Make both timezone-aware or both naive
    if value.tzinfo is None and now.tzinfo is not None:
        value = value.replace(tzinfo=timezone.utc)
    elif value.tzinfo is not None and now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    
    delta = (value.date() - now.date()).days
    
    if delta == 0:
        return "today"
    elif delta == 1:
        return "tomorrow"
    elif delta == -1:
        return "yesterday"
    else:
        return value.strftime(format)


def naturaldate(value, format='%b %d', when=None):
    """
    Return a natural date representation (alias for naturalday).
    """
    return naturalday(value, format=format, when=when)


def precisedelta(value, minimum_unit="seconds", suppress=None, format="%0.0f"):
    """
    Return a precise representation of a timedelta.
    
    Args:
        value: timedelta or number of seconds
        minimum_unit: Minimum unit to display
        suppress: List of units to suppress
        format: Format string for numbers
        
    Returns:
        String like "2 hours and 3 minutes"
    """
    if isinstance(value, timedelta):
        total_seconds = value.total_seconds()
    else:
        try:
            total_seconds = float(value)
        except (ValueError, TypeError):
            return str(value)
    
    if suppress is None:
        suppress = []
    
    abs_seconds = abs(total_seconds)
    
    # Calculate each unit
    years = int(abs_seconds // (365.25 * 24 * 3600))
    abs_seconds -= years * 365.25 * 24 * 3600
    
    months = int(abs_seconds // (30.44 * 24 * 3600))
    abs_seconds -= months * 30.44 * 24 * 3600
    
    days = int(abs_seconds // (24 * 3600))
    abs_seconds -= days * 24 * 3600
    
    hours = int(abs_seconds // 3600)
    abs_seconds -= hours * 3600
    
    minutes = int(abs_seconds // 60)
    abs_seconds -= minutes * 60
    
    seconds = abs_seconds
    
    # Build parts list
    parts = []
    
    if years > 0 and "years" not in suppress:
        parts.append("%d year%s" % (years, "s" if years != 1 else ""))
    
    if months > 0 and "months" not in suppress:
        parts.append("%d month%s" % (months, "s" if months != 1 else ""))
    
    if days > 0 and "days" not in suppress:
        parts.append("%d day%s" % (days, "s" if days != 1 else ""))
    
    if hours > 0 and "hours" not in suppress and minimum_unit not in ["days", "months", "years"]:
        parts.append("%d hour%s" % (hours, "s" if hours != 1 else ""))
    
    if minutes > 0 and "minutes" not in suppress and minimum_unit not in ["hours", "days", "months", "years"]:
        parts.append("%d minute%s" % (minutes, "s" if minutes != 1 else ""))
    
    if minimum_unit == "seconds" and "seconds" not in suppress:
        if seconds >= 1 or len(parts) == 0:
            sec_val = format % seconds
            parts.append("%s second%s" % (sec_val, "s" if seconds != 1 else ""))
    
    if len(parts) == 0:
        if minimum_unit == "minutes":
            return "0 minutes"
        elif minimum_unit == "hours":
            return "0 hours"
        elif minimum_unit == "days":
            return "0 days"
        else:
            return "0 seconds"
    
    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        return parts[0] + " and " + parts[1]
    else:
        return ", ".join(parts[:-1]) + " and " + parts[-1]