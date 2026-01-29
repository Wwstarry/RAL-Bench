from datetime import timedelta, datetime


def precisedelta(delta):
    """
    Convert a timedelta or seconds into a precise human-readable duration.
    Example: timedelta(days=1, seconds=3600) -> '1 day, 1 hour'
    """
    if isinstance(delta, (int, float)):
        delta = timedelta(seconds=delta)
    if not isinstance(delta, timedelta):
        raise ValueError("precisedelta expects a timedelta or seconds value.")

    days = delta.days
    seconds = delta.seconds
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

    return ", ".join(parts)


def naturaldelta(delta):
    """
    Convert a timedelta or seconds into a rounded human-readable duration.
    Example: timedelta(days=1, seconds=3600) -> '1 day'
    """
    if isinstance(delta, (int, float)):
        delta = timedelta(seconds=delta)
    if not isinstance(delta, timedelta):
        raise ValueError("naturaldelta expects a timedelta or seconds value.")

    days = delta.days
    seconds = delta.seconds
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    if days >= 1:
        return f"{days} day{'s' if days != 1 else ''}"
    elif hours >= 1:
        return f"{hours} hour{'s' if hours != 1 else ''}"
    elif minutes >= 1:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        return f"{seconds} second{'s' if seconds != 1 else ''}"


def naturaltime(value):
    """
    Convert a datetime or timedelta into a human-readable relative time.
    Example: datetime.now() - timedelta(days=1) -> 'a day ago'
    """
    now = datetime.now()
    if isinstance(value, timedelta):
        value = now - value
    if not isinstance(value, datetime):
        raise ValueError("naturaltime expects a datetime or timedelta value.")

    delta = now - value
    if delta.days > 0:
        return f"{naturaldelta(delta)} ago"
    elif delta.days < 0:
        return f"in {naturaldelta(-delta)}"
    else:
        return "just now"