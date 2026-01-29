"""Human-readable times and dates."""

import datetime
from .i18n import gettext as _, ngettext
from .lists import humanize_list

# Constants for time calculations
# Using integer arithmetic where possible is better for precision
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400
# Average days per month/year for approximation
DAYS_PER_MONTH = 30.436875
DAYS_PER_YEAR = 365.2425


def _now():
    """Wrapper for datetime.datetime.now() to allow for mocking in tests."""
    return datetime.datetime.now()


def precisedelta(d, minimum_unit="seconds", suppress=(), format="%0.2f"):
    """
    Formats a timedelta object or seconds into a human-readable, precise string.
    """
    if isinstance(d, datetime.timedelta):
        delta = d
    else:
        try:
            delta = datetime.timedelta(seconds=float(d))
        except (ValueError, TypeError):
            return str(d)

    if delta.total_seconds() < 0:
        return str(d)

    days = delta.days
    seconds = delta.seconds
    microseconds = delta.microseconds

    years, days = divmod(days, DAYS_PER_YEAR)
    months, days = divmod(days, DAYS_PER_MONTH)
    hours, seconds = divmod(seconds, SECONDS_PER_HOUR)
    minutes, seconds = divmod(seconds, SECONDS_PER_MINUTE)

    years = int(years)
    months = int(months)
    days = int(days)

    total_seconds_remainder = seconds + microseconds / 1_000_000.0

    units = {
        "year": years,
        "month": months,
        "day": days,
        "hour": hours,
        "minute": minutes,
        "second": total_seconds_remainder,
    }

    unit_order = ["year", "month", "day", "hour", "minute", "second"]

    try:
        min_unit_index = unit_order.index(minimum_unit)
    except ValueError:
        min_unit_index = 5  # Default to seconds

    parts = []
    for i, name in enumerate(unit_order):
        if name in suppress:
            continue

        value = units[name]

        if i < min_unit_index:
            value = int(value)
            if value > 0:
                parts.append(ngettext("%d " + name, "%d " + name + "s", value) % value)
        elif i == min_unit_index:
            if value > 0:
                formatted_value = format % value
                is_singular = 0.99 < value < 1.01
                if is_singular:
                    parts.append(_(f"{formatted_value} {name}"))
                else:
                    parts.append(_(f"{formatted_value} {name}s"))
            break
        else:
            break

    if not parts:
        return ngettext(f"0 {minimum_unit}", f"0 {minimum_unit}s", 0)

    return humanize_list(parts, conjunction=_("and"))


def naturaldelta(value, months=True, minimum_unit="seconds"):
    """
    Formats a timedelta or seconds into a human-readable, but not precise, string.
    """
    if isinstance(value, datetime.timedelta):
        delta = value
    else:
        try:
            delta = datetime.timedelta(seconds=float(value))
        except (ValueError, TypeError):
            return str(value)

    total_seconds = abs(delta.total_seconds())

    units = [
        ("year", DAYS_PER_YEAR * SECONDS_PER_DAY),
        ("month", DAYS_PER_MONTH * SECONDS_PER_DAY),
        ("day", SECONDS_PER_DAY),
        ("hour", SECONDS_PER_HOUR),
        ("minute", SECONDS_PER_MINUTE),
        ("second", 1),
    ]

    if not months:
        units = [u for u in units if u[0] != "month"]

    unit_names = [u[0] for u in units]
    try:
        min_unit_index = unit_names.index(minimum_unit)
    except ValueError:
        min_unit_index = len(units) - 1

    for i, (name, seconds_in_unit) in enumerate(units):
        if i > min_unit_index:
            continue

        count = total_seconds / seconds_in_unit
        if count >= 1.0:
            count = int(round(count))
            return ngettext(f"{count} {name}", f"{count} {name}s", count)

    if total_seconds == 0:
        return _("a moment")

    return ngettext(f"1 {minimum_unit}", f"1 {minimum_unit}s", 1)


def naturaltime(value, future=False, months=True, minimum_unit="seconds", when=None):
    """
    Formats a datetime, date, or seconds into a human-readable string like "2 hours ago".
    """
    now = when or _now()

    if isinstance(value, (int, float)):
        delta = datetime.timedelta(seconds=value)
        dt = now - delta if not future else now + delta
    elif isinstance(value, datetime.datetime):
        dt = value
    elif isinstance(value, datetime.date):
        dt = datetime.datetime.combine(value, datetime.time.min)
    else:
        return str(value)

    now_is_aware = now.tzinfo is not None and now.tzinfo.utcoffset(now) is not None
    dt_is_aware = dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None

    if now_is_aware != dt_is_aware:
        now = now.replace(tzinfo=None)
        dt = dt.replace(tzinfo=None)

    delta = now - dt
    is_future = delta.total_seconds() < 0

    if abs(delta.total_seconds()) < 1:
        return _("now")

    human_delta = naturaldelta(delta, months=months, minimum_unit=minimum_unit)

    if is_future:
        return _("%s from now") % human_delta
    else:
        return _("%s ago") % human_delta