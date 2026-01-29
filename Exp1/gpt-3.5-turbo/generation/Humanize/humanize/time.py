import datetime
import time as _time

from .i18n import _


def naturaltime(value, future=False):
    """
    Return a natural representation of a time difference between now and value.
    value can be a datetime, date, or a timedelta.
    """
    now = datetime.datetime.now()
    if isinstance(value, datetime.timedelta):
        delta = value
    elif isinstance(value, datetime.datetime):
        delta = now - value
    elif isinstance(value, datetime.date):
        delta = now.date() - value
        delta = datetime.timedelta(days=delta.days)
    else:
        return str(value)

    seconds = delta.total_seconds()
    if seconds < 0:
        seconds = abs(seconds)
        future = True

    if seconds < 10:
        return _("just now") if not future else _("in a moment")
    if seconds < 60:
        count = int(seconds)
        return _("%d seconds ago") % count if not future else _("in %d seconds") % count
    if seconds < 3600:
        count = int(seconds // 60)
        return _("%d minutes ago") % count if not future else _("in %d minutes") % count
    if seconds < 86400:
        count = int(seconds // 3600)
        return _("%d hours ago") % count if not future else _("in %d hours") % count
    if seconds < 604800:
        count = int(seconds // 86400)
        return _("%d days ago") % count if not future else _("in %d days") % count
    if seconds < 2419200:
        count = int(seconds // 604800)
        return _("%d weeks ago") % count if not future else _("in %d weeks") % count
    # fallback to date string
    if isinstance(value, datetime.datetime):
        return value.strftime("%b %d, %Y")
    elif isinstance(value, datetime.date):
        return value.strftime("%b %d, %Y")
    else:
        return str(value)


def naturaldelta(delta, months=True):
    """
    Return a natural representation of a timedelta.
    """
    if not isinstance(delta, datetime.timedelta):
        return str(delta)

    seconds = int(abs(delta.total_seconds()))
    future = delta.total_seconds() < 0

    periods = (
        (60 * 60 * 24 * 365, _("year"), _("years")),
        (60 * 60 * 24 * 30, _("month"), _("months")) if months else None,
        (60 * 60 * 24 * 7, _("week"), _("weeks")),
        (60 * 60 * 24, _("day"), _("days")),
        (60 * 60, _("hour"), _("hours")),
        (60, _("minute"), _("minutes")),
        (1, _("second"), _("seconds")),
    )
    periods = [p for p in periods if p]

    for period_seconds, singular, plural in periods:
        if seconds >= period_seconds:
            count = seconds // period_seconds
            if count == 1:
                s = singular
            else:
                s = plural
            if future:
                return _("in %(count)d %(unit)s") % {"count": count, "unit": s}
            else:
                return _("%(count)d %(unit)s") % {"count": count, "unit": s}
    return _("0 seconds")


def precisedelta(delta, format="%0.0f %s", minimum_unit="second", suppress=["0 seconds"]):
    """
    Return a precise representation of a timedelta, showing all units down to minimum_unit.
    format is a format string with two placeholders: value and unit.
    suppress is a list of strings to suppress from output.
    """
    import math

    if not isinstance(delta, datetime.timedelta):
        return str(delta)

    seconds = int(abs(delta.total_seconds()))
    future = delta.total_seconds() < 0

    units = [
        ("year", 60 * 60 * 24 * 365),
        ("month", 60 * 60 * 24 * 30),
        ("week", 60 * 60 * 24 * 7),
        ("day", 60 * 60 * 24),
        ("hour", 60 * 60),
        ("minute", 60),
        ("second", 1),
    ]

    # Find index of minimum_unit
    min_index = 6  # default to second
    for i, (name, _) in enumerate(units):
        if name == minimum_unit:
            min_index = i
            break

    parts = []
    for name, count_seconds in units[: min_index + 1]:
        value = seconds // count_seconds
        seconds = seconds % count_seconds
        if value > 0:
            unit = name if value == 1 else name + "s"
            part = format % (value, unit)
            if part not in suppress:
                parts.append(part)

    if not parts:
        parts.append("0 seconds")

    result = ", ".join(parts)
    if future:
        return _("in %(delta)s") % {"delta": result}
    else:
        return result