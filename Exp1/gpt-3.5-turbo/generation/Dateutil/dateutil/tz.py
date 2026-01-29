"""
Pure Python implementation of dateutil.tz module with tz.UTC and tz.gettz
for timezone-aware datetime support.
"""

import datetime
import threading

__all__ = ['UTC', 'gettz', 'tzoffset']

class _UTC(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(0)
    def tzname(self, dt):
        return "UTC"
    def dst(self, dt):
        return datetime.timedelta(0)
    def __repr__(self):
        return "<UTC>"

UTC = _UTC()

class tzoffset(datetime.tzinfo):
    """
    Fixed offset in seconds east from UTC.
    """
    def __init__(self, name, offset):
        self._name = name
        self._offset = datetime.timedelta(seconds=offset)

    def utcoffset(self, dt):
        return self._offset

    def tzname(self, dt):
        return self._name

    def dst(self, dt):
        return datetime.timedelta(0)

    def __repr__(self):
        return f"<tzoffset {self._name} {self._offset}>"

# Simple cache for gettz
_tz_cache = {}
_tz_cache_lock = threading.Lock()

def gettz(name):
    """
    Return a tzinfo object corresponding to the given timezone name.

    Supports:
        - 'UTC' or 'utc' returns UTC tzinfo
        - Offsets like '+HH:MM', '-HHMM', '+HHMMSS'
        - Common timezone abbreviations: 'EST', 'EDT', 'CST', 'CDT', 'MST', 'MDT', 'PST', 'PDT'
        - 'local' returns local timezone (not implemented, returns None)
    """
    if not name:
        return None
    name = name.strip()
    if name.upper() == 'UTC':
        return UTC

    with _tz_cache_lock:
        if name in _tz_cache:
            return _tz_cache[name]

    # Parse offset formats
    # Examples: +05:30, -0400, +0230, -07:00
    m = _offset_re.match(name)
    if m:
        sign = 1 if m.group('sign') == '+' else -1
        hh = int(m.group('hour'))
        mm = int(m.group('minute') or 0)
        ss = int(m.group('second') or 0)
        offset = sign * (hh*3600 + mm*60 + ss)
        tz = tzoffset(name, offset)
        with _tz_cache_lock:
            _tz_cache[name] = tz
        return tz

    # Common US timezones with fixed offsets (no DST handling)
    _common_tz = {
        'EST': -5*3600,
        'EDT': -4*3600,
        'CST': -6*3600,
        'CDT': -5*3600,
        'MST': -7*3600,
        'MDT': -6*3600,
        'PST': -8*3600,
        'PDT': -7*3600,
    }
    key = name.upper()
    if key in _common_tz:
        tz = tzoffset(name, _common_tz[key])
        with _tz_cache_lock:
            _tz_cache[name] = tz
        return tz

    # Local timezone not implemented, return None
    return None

_offset_re = None
def _init_offset_re():
    global _offset_re
    if _offset_re is None:
        import re
        _offset_re = re.compile(
            r'^(?P<sign>[+\-])'
            r'(?P<hour>\d{2})'
            r':?(?P<minute>\d{2})?'
            r':?(?P<second>\d{2})?$'
        )
_init_offset_re()