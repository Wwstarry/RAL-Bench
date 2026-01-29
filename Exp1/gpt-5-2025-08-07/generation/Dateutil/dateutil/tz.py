from datetime import timedelta, tzinfo, timezone
import re

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None


class tzutc(tzinfo):
    def utcoffset(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return timedelta(0)

    def __repr__(self):
        return "tzutc()"


UTC = tzutc()


class tzoffset(tzinfo):
    """
    Fixed-offset timezone with a name and offset in seconds.
    """
    def __init__(self, name, offset):
        self._name = name
        if isinstance(offset, int):
            self._offset = timedelta(seconds=offset)
        elif isinstance(offset, timedelta):
            self._offset = offset
        else:
            raise TypeError("offset must be int seconds or timedelta")

    def utcoffset(self, dt):
        return self._offset

    def tzname(self, dt):
        return self._name

    def dst(self, dt):
        return timedelta(0)

    def __repr__(self):
        return "tzoffset(%r, %r)" % (self._name, int(self._offset.total_seconds()))


# Fallback fixed-offset names for common zones if ZoneInfo not available
_FALLBACK_FIXED = {
    "UTC": tzoffset("UTC", 0),
    "Etc/UTC": tzoffset("Etc/UTC", 0),
    "GMT": tzoffset("GMT", 0),
    "Etc/GMT": tzoffset("Etc/GMT", 0),
    "US/Eastern": tzoffset("US/Eastern", -5 * 3600),
    "US/Central": tzoffset("US/Central", -6 * 3600),
    "US/Mountain": tzoffset("US/Mountain", -7 * 3600),
    "US/Pacific": tzoffset("US/Pacific", -8 * 3600),
    "America/New_York": tzoffset("America/New_York", -5 * 3600),
    "America/Chicago": tzoffset("America/Chicago", -6 * 3600),
    "America/Denver": tzoffset("America/Denver", -7 * 3600),
    "America/Los_Angeles": tzoffset("America/Los_Angeles", -8 * 3600),
    "Europe/London": tzoffset("Europe/London", 0),
    "Europe/Paris": tzoffset("Europe/Paris", 1 * 3600),
}


def _parse_utc_offset_str(s):
    """
    Parse strings like 'UTC+02:00', 'UTC-0500', 'GMT+1' into tzoffset.
    """
    m = re.match(r'^(?:UTC|GMT)\s*([+\-])\s*(\d{1,2})(?::?(\d{2}))?$', s, re.IGNORECASE)
    if m:
        sign = 1 if m.group(1) == '+' else -1
        hours = int(m.group(2))
        minutes = int(m.group(3) or "0")
        return tzoffset(s, sign * (hours * 3600 + minutes * 60))
    # Plain offset like +02:00 or -0500
    m2 = re.match(r'^([+\-])(\d{2}):?(\d{2})$', s)
    if m2:
        sign = 1 if m2.group(1) == '+' else -1
        hours = int(m2.group(2))
        minutes = int(m2.group(3))
        return tzoffset(s, sign * (hours * 3600 + minutes * 60))
    return None


def gettz(name=None):
    """
    Get a tzinfo for the given time zone name.

    Behavior:
    - If name is None or 'UTC'/'Etc/UTC'/'GMT', returns UTC
    - Uses zoneinfo.ZoneInfo when available for IANA zone names
    - Parses 'UTC+HH:MM' or offset strings into fixed offset tzinfo
    - Falls back to a small set of fixed-offset mappings for common names
    """
    if name is None:
        return UTC

    if isinstance(name, str):
        key = name.strip()
    else:
        return None

    if key.upper() in ("UTC", "ETC/UTC", "GMT", "ETC/GMT", "Z"):
        # return a canonical UTC tzinfo
        if ZoneInfo is not None:
            try:
                return ZoneInfo("UTC")
            except Exception:
                return UTC
        return UTC

    # parse offset forms
    off = _parse_utc_offset_str(key)
    if off:
        return off

    if ZoneInfo is not None:
        try:
            return ZoneInfo(key)
        except Exception:
            pass

    # fallback fixed offsets
    return _FALLBACK_FIXED.get(key)