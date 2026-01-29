# -*- coding: utf-8 -*-

import datetime as _dt

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:
    # Basic fallback for Python < 3.9
    from datetime import timezone as _py_timezone, timedelta as _py_timedelta
    
    class ZoneInfoNotFoundError(Exception):
        pass

    class ZoneInfo:
        def __init__(self, key):
            if key.upper() != "UTC":
                raise ZoneInfoNotFoundError(f"Timezone '{key}' not found. This fallback only supports 'UTC'.")
            self._key = "UTC"
            self._offset = _py_timedelta(0)

        def utcoffset(self, dt):
            return self._offset

        def dst(self, dt):
            return None

        def tzname(self, dt):
            return self._key

        def fromutc(self, dt):
            return (dt + self._offset).replace(tzinfo=self)
        
        def localize(self, dt):
            if dt.tzinfo is not None:
                raise ValueError("Not a naive datetime")
            return dt.replace(tzinfo=self)


class Timezone(ZoneInfo):
    """
    A wrapper for zoneinfo.ZoneInfo to provide a consistent API.
    """
    def __init__(self, name):
        try:
            super().__init__(name)
        except ZoneInfoNotFoundError:
            # Handle some common aliases
            if name.upper() == "LOCAL":
                # This is a simplification; true local timezone is complex
                tz_name = _dt.datetime.now().astimezone().tzname()
                if tz_name and tz_name != name:
                    try:
                        super().__init__(tz_name)
                        return
                    except ZoneInfoNotFoundError:
                        pass # Fall through to raise error with original name
            raise ValueError(f"Unknown timezone '{name}'")

    def __repr__(self):
        return f"Timezone('{self.key}')"

    def __str__(self):
        return self.key


# Pre-defined timezones
UTC = Timezone("UTC")

def local_timezone():
    """
    Returns the system's local timezone.
    """
    # This is a best-effort implementation. Real Pendulum has a more robust detection mechanism.
    try:
        # Python 3.9+
        local_tz_name = _dt.datetime.now().astimezone().tzname()
        if local_tz_name:
            return Timezone(local_tz_name)
    except Exception:
        pass
    
    # Fallback to UTC if detection fails
    return UTC