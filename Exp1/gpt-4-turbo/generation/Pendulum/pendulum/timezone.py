import time
import re
from datetime import tzinfo, timedelta, datetime as _dt

class Timezone(tzinfo):
    def __init__(self, name, offset=None):
        self.name = name
        if offset is None:
            self._offset = self._get_offset_from_name(name)
        else:
            self._offset = offset

    def utcoffset(self, dt):
        return timedelta(seconds=self._offset)

    def dst(self, dt):
        # No DST support in pure Python implementation
        return timedelta(0)

    def tzname(self, dt):
        return self.name

    def __repr__(self):
        return f"<Timezone {self.name}>"

    @staticmethod
    def _get_offset_from_name(name):
        # Support UTC, UTC+X, UTC-X, and common timezones
        if name.upper() == "UTC":
            return 0
        m = re.match(r"UTC([+-])(\d{1,2})(?::(\d{2}))?$", name.upper())
        if m:
            sign = 1 if m.group(1) == "+" else -1
            hours = int(m.group(2))
            minutes = int(m.group(3) or 0)
            return sign * (hours * 3600 + minutes * 60)
        # Fallback: treat as UTC
        return 0

def timezone(name):
    return Timezone(name)

def local_timezone():
    # Try to get local offset
    if time.daylight and time.localtime().tm_isdst:
        offset = -time.altzone
    else:
        offset = -time.timezone
    # Format as UTC+/-HH:MM
    hours = offset // 3600
    minutes = abs(offset % 3600) // 60
    sign = "+" if hours >= 0 else "-"
    tzname = f"UTC{sign}{abs(hours):02d}:{minutes:02d}"
    return Timezone(tzname, offset)