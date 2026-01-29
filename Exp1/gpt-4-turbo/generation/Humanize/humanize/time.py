import datetime

def _parse_timedelta(delta):
    """
    Returns (days, hours, minutes, seconds, microseconds) from timedelta.
    """
    days = delta.days
    seconds = delta.seconds
    microseconds = delta.microseconds
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return days, hours, minutes, seconds, microseconds

def _pluralize(value, unit):
    if value == 1:
        return f"{value} {unit}"
    else:
        return f"{value} {unit}s"

def precisedelta(delta, minimum_unit="seconds", suppress=[]):
    """
    Returns a detailed, precise delta string.
    """
    if isinstance(delta, (int, float)):
        delta = datetime.timedelta(seconds=delta)
    days, hours, minutes, seconds, microseconds = _parse_timedelta(delta)
    parts = []
    if "days" not in suppress and (days or minimum_unit == "days"):
        parts.append(_pluralize(days, "day"))
    if "hours" not in suppress and (hours or (not parts and minimum_unit == "hours")):
        parts.append(_pluralize(hours, "hour"))
    if "minutes" not in suppress and (minutes or (not parts and minimum_unit == "minutes")):
        parts.append(_pluralize(minutes, "minute"))
    if "seconds" not in suppress and (seconds or (not parts and minimum_unit == "seconds")):
        parts.append(_pluralize(seconds, "second"))
    if "microseconds" not in suppress and (microseconds or (not parts and minimum_unit == "microseconds")):
        parts.append(_pluralize(microseconds, "microsecond"))
    return ", ".join(parts)

def naturaldelta(delta):
    """
    Returns a humanized delta string, e.g. '3 minutes'.
    """
    if isinstance(delta, (int, float)):
        delta = datetime.timedelta(seconds=delta)
    days, hours, minutes, seconds, microseconds = _parse_timedelta(delta)
    if days:
        return _pluralize(days, "day")
    if hours:
        return _pluralize(hours, "hour")
    if minutes:
        return _pluralize(minutes, "minute")
    if seconds:
        return _pluralize(seconds, "second")
    return _pluralize(microseconds, "microsecond")

def naturaltime(value, when=None):
    """
    Returns a humanized string representing time difference, e.g. '3 minutes ago'.
    """
    if value is None:
        return ""
    if when is None:
        when = datetime.datetime.now()
    if isinstance(value, datetime.timedelta):
        delta = value
        ago = delta.total_seconds() < 0
        delta = abs(delta)
        if delta < datetime.timedelta(seconds=1):
            return "now"
        s = naturaldelta(delta)
        return f"{s} ago" if ago else f"in {s}"
    if not isinstance(value, datetime.datetime):
        # Assume value is seconds in the past
        value = when - datetime.timedelta(seconds=float(value))
    delta = when - value
    ago = delta.total_seconds() >= 0
    delta = abs(delta)
    if delta < datetime.timedelta(seconds=1):
        return "now"
    s = naturaldelta(delta)
    return f"{s} ago" if ago else f"in {s}"