import datetime as _dt
import re
import time
try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None

UTC = _dt.timezone.utc


class FixedOffset(_dt.tzinfo):
    """
    Fixed offset timezone, e.g., +02:00 or -05:30.
    """

    def __init__(self, minutes_offset: int, name: str = None):
        self._offset = _dt.timedelta(minutes=minutes_offset)
        sign = "+" if minutes_offset >= 0 else "-"
        minutes_offset = abs(minutes_offset)
        hours = minutes_offset // 60
        minutes = minutes_offset % 60
        self._name = name or f"{sign}{hours:02d}:{minutes:02d}"

    def utcoffset(self, dt):
        return self._offset

    def tzname(self, dt):
        return self._name

    def dst(self, dt):
        return _dt.timedelta(0)

    def __repr__(self):
        return f"FixedOffset({self._name})"

    def __str__(self):
        return self._name


def _parse_offset_string(s: str):
    """
    Parses '+HH:MM', '-HHMM', '+HH' and returns minutes offset.
    """
    m = re.fullmatch(r"([+-])(\d{2})(?::?(\d{2}))?$", s)
    if not m:
        return None
    sign = 1 if m.group(1) == "+" else -1
    hours = int(m.group(2))
    minutes = int(m.group(3) or 0)
    return sign * (hours * 60 + minutes)


def _local_fixed_offset():
    """
    Returns a FixedOffset representing the current local timezone offset.
    """
    is_dst = time.localtime().tm_isdst > 0
    if is_dst and hasattr(time, "altzone"):
        offset_seconds = -time.altzone
    else:
        offset_seconds = -time.timezone
    minutes = int(offset_seconds // 60)
    return FixedOffset(minutes, name="local")


def timezone(name_or_offset):
    """
    Return a tzinfo for a timezone name or offset string.

    Known names:
    - 'UTC', 'Etc/UTC', 'Z' -> UTC
    - 'local' -> local fixed offset
    Else: tries zoneinfo.ZoneInfo and falls back to parsing offset strings.
    """
    if name_or_offset is None:
        return None
    if isinstance(name_or_offset, _dt.tzinfo):
        return name_or_offset
    if not isinstance(name_or_offset, str):
        raise TypeError("timezone() expects a str or tzinfo")

    name = name_or_offset.strip()

    if name.upper() in ("UTC", "ETC/UTC", "Z"):
        return UTC
    if name.lower() == "local":
        return _local_fixed_offset()

    # Offset string
    minutes = _parse_offset_string(name)
    if minutes is not None:
        return FixedOffset(minutes)

    # ZoneInfo
    if ZoneInfo is not None:
        try:
            return ZoneInfo(name)
        except Exception:
            pass

    # Fallback: unknown timezone, try offset-like pattern with sign omitted or raise
    raise ValueError(f"Unknown timezone: {name_or_offset}")