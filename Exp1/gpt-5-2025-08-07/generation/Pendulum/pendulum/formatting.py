def pluralize(value: int, singular: str, plural: str = None) -> str:
    if plural is None:
        plural = singular + "s"
    if value == 1:
        return f"1 {singular}"
    return f"{value} {plural}"


def humanize_duration(seconds: float, absolute: bool = False) -> str:
    """
    Very simple English humanization for a diff in seconds.

    Chooses the largest unit among years, months, days, hours, minutes, seconds.
    Approximations:
      - 1 month = 30 days
      - 1 year = 365 days
    """
    sign = 1 if seconds >= 0 else -1
    seconds = abs(int(round(seconds)))

    # Units
    minute = 60
    hour = 3600
    day = 86400
    month = 30 * day
    year = 365 * day

    if seconds >= year:
        v = seconds // year
        text = pluralize(v, "year")
    elif seconds >= month:
        v = seconds // month
        text = pluralize(v, "month")
    elif seconds >= day:
        v = seconds // day
        text = pluralize(v, "day")
    elif seconds >= hour:
        v = seconds // hour
        text = pluralize(v, "hour")
    elif seconds >= minute:
        v = seconds // minute
        text = pluralize(v, "minute")
    else:
        v = max(seconds, 0)
        text = pluralize(v, "second")

    # absolute means caller will add direction themselves
    return text