from datetime import tzinfo, timedelta, datetime
import time

class tzoffset(tzinfo):
    def __init__(self, name, offset):
        self._name = name
        self._offset = int(offset)

    def utcoffset(self, dt):
        return timedelta(seconds=self._offset)

    def dst(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return self._name or f"UTC{self._offset // 3600:+03d}:{abs(self._offset % 3600) // 60:02d}"

    def __repr__(self):
        return f"tzoffset({self._name!r}, {self._offset})"

class _UTC(tzinfo):
    def utcoffset(self, dt):
        return timedelta(0)

    def dst(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def __repr__(self):
        return "UTC"

UTC = _UTC()

def gettz(name):
    """
    Return a tzinfo object for a named time zone.
    Only supports a few common zones for test compatibility.
    """
    if name is None:
        return None
    if name.upper() in ("UTC", "Z"):
        return UTC
    # Try to parse offset: "+HH:MM" or "-HH:MM"
    import re
    m = re.match(r"([+-])(\d{2}):?(\d{2})", name)
    if m:
        sign = 1 if m.group(1) == "+" else -1
        hours = int(m.group(2))
        minutes = int(m.group(3))
        offset = sign * (hours * 3600 + minutes * 60)
        return tzoffset(name, offset)
    # Fallback: support a few common zones
    _COMMON_ZONES = {
        "EST": -18000,
        "EDT": -14400,
        "CST": -21600,
        "CDT": -18000,
        "MST": -25200,
        "MDT": -21600,
        "PST": -28800,
        "PDT": -25200,
        "GMT": 0,
        "BST": 3600,
        "CET": 3600,
        "CEST": 7200,
        "EET": 7200,
        "EEST": 10800,
        "JST": 32400,
        "AEST": 36000,
        "AEDT": 39600,
        "ACST": 34200,
        "ACDT": 37800,
        "AWST": 28800,
    }
    offset = _COMMON_ZONES.get(name.upper())
    if offset is not None:
        return tzoffset(name, offset)
    return None