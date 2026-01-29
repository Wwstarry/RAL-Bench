import datetime
from .i18n import gettext as _, ngettext, pgettext


def _now():
    """A hook for testing."""
    return datetime.datetime.now()


def _utcnow():
    """A hook for testing."""
    return datetime.datetime.utcnow()


def _is_aware(d):
    """Checks if a datetime object is timezone-aware."""
    return d.tzinfo is not None and d.tzinfo.utcoffset(d) is not None


def precisedelta(d, minimum_unit="seconds", suppress=(), format="%0.2f"):
    """Formats a timedelta object with arbitrary precision."""
    if isinstance(d, (int, float)):
        d = datetime.timedelta(seconds=d)
    elif not isinstance(d, datetime.timedelta):
        return d

    periods = [
        ("year", "years", 31556926),
        ("month", "months", 2629743),
        ("day", "days", 86400),
        ("hour", "hours", 3600),
        ("minute", "minutes", 60),
        ("second", "seconds", 1),
    ]

    seconds = d.total_seconds()
    if seconds == 0 and minimum_unit == "seconds":
        return _("0 seconds")

    parts = []
    for singular, plural, secs_in_unit in periods:
        if singular + "s" in suppress or singular in suppress:
            continue

        if abs(seconds) >= secs_in_unit:
            count = int(seconds / secs_in_unit)
            seconds -= count * secs_in_unit
            parts.append(ngettext(f"1 {singular}", f"{count} {plural}", count))

        if singular == minimum_unit:
            if abs(seconds) > 0:
                sec_str = format % seconds
                if "." in sec_str:
                    sec_str = sec_str.rstrip("0").rstrip(".")
                unit_str = ngettext("second", "seconds", float(sec_str))
                parts.append(f"{sec_str} {unit_str}")
            break

    if not parts:
        return _("0 seconds")

    if len(parts) == 1:
        return parts[0]

    return ", ".join(parts[:-1]) + " " + _("and") + " " + parts[-1]


def naturaldelta(value, months=True, minimum_unit="seconds"):
    """Formats a timedelta or seconds into a human-readable string."""
    if isinstance(value, (int, float)):
        delta = datetime.timedelta(seconds=value)
    elif isinstance(value, datetime.timedelta):
        delta = value
    else:
        return value

    seconds = abs(delta.total_seconds())

    if seconds < 1 and minimum_unit == "seconds":
        return _("a moment")

    periods = [
        ("year", "years", 31556926 if months else 31536000),
        ("month", "months", 2629743),
        ("day", "days", 86400),
        ("hour", "hours", 3600),
        ("minute", "minutes", 60),
        ("second", "seconds", 1),
    ]

    if not months:
        periods.pop(1)

    parts = []
    for singular, plural, secs_in_unit in periods:
        if minimum_unit in (singular, plural):
            count = round(seconds / secs_in_unit)
            if count > 0:
                parts.append(ngettext(f"1 {singular}", f"{count} {plural}", count))
            break

        if seconds >= secs_in_unit:
            count = int(seconds / secs_in_unit)
            seconds -= count * secs_in_unit
            parts.append(ngettext(f"1 {singular}", f"{count} {plural}", count))

    if not parts:
        return _("a moment")

    if len(parts) == 1:
        return parts[0]

    return ", ".join(parts[:-1]) + " " + _("and") + " " + parts[-1]


def naturaltime(value, future=False, months=True, minimum_unit="seconds", when=None):
    """Formats a datetime into a relative time string."""
    if when is None:
        if isinstance(value, datetime.datetime) and _is_aware(value):
            when = datetime.datetime.now(datetime.timezone.utc)
        else:
            when = _now()

    if isinstance(value, (int, float)):
        value = datetime.datetime.fromtimestamp(value)
    
    if not isinstance(value, datetime.datetime):
        return value

    if _is_aware(value) and not _is_aware(when):
        when = when.astimezone()
    elif not _is_aware(value) and _is_aware(when):
        value = value.astimezone()

    delta = when - value

    if future:
        delta = -delta
        ago = pgettext("naturaltime-future", " from now")
        now_str = pgettext("naturaltime-future", "now")
    else:
        ago = pgettext("naturaltime", " ago")
        now_str = pgettext("naturaltime", "now")

    seconds = abs(delta.total_seconds())

    if seconds < 1:
        return now_str
    
    if seconds < 60 and minimum_unit == "seconds":
        return _("a moment") + ago

    human_delta = naturaldelta(delta, months=months, minimum_unit=minimum_unit)
    
    if human_delta == _("a moment"):
        return now_str

    return human_delta + ago


def naturalday(value, format="%b %d"):
    """Returns "today", "yesterday", "tomorrow" or a formatted date string."""
    if isinstance(value, datetime.datetime):
        value = value.date()
    elif isinstance(value, (int, float)):
        value = datetime.date.fromtimestamp(value)

    if not isinstance(value, datetime.date):
        return value

    today = datetime.date.today()
    delta = value - today

    if delta.days == 0:
        return _("today")
    if delta.days == 1:
        return _("tomorrow")
    if delta.days == -1:
        return _("yesterday")

    return value.strftime(format)


def naturaldate(value):
    """Like naturalday, but returns a full date if not today/yesterday/tomorrow."""
    return naturalday(value, format="%b %d, %Y")