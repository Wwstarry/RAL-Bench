from datetime import tzinfo as _tzinfo, timedelta as _timedelta, datetime as _datetime
import re

class Timezone(_tzinfo):
    __slots__ = ("_name", "_offset")

    _offset_pattern = re.compile(r"^([+-])(\d{2}):?(\d{2})$")

    def __init__(self, name, offset=None):
        self._name = name
        if offset is not None:
            if isinstance(offset, _timedelta):
                self._offset = offset
            else:
                raise TypeError("offset must be a datetime.timedelta instance or None")
        else:
            # Parse offset from name if possible
            self._offset = self._parse_offset_from_name(name)

    def _parse_offset_from_name(self, name):
        if name == "UTC" or name == "Z":
            return _timedelta(0)
        m = self._offset_pattern.match(name)
        if m:
            sign, hh, mm = m.groups()
            hh = int(hh)
            mm = int(mm)
            delta = _timedelta(hours=hh, minutes=mm)
            if sign == "-":
                delta = -delta
            return delta
        # Unknown offset, default to zero
        return _timedelta(0)

    def utcoffset(self, dt):
        return self._offset

    def tzname(self, dt):
        return self._name

    def dst(self, dt):
        return _timedelta(0)

    def __repr__(self):
        return f"<Timezone [{self._name}]>"

    def __eq__(self, other):
        if not isinstance(other, Timezone):
            return False
        return self._offset == other._offset and self._name == other._name


# Cache for timezone instances
_timezone_cache = {}

def timezone(name):
    if not isinstance(name, str):
        raise TypeError("timezone name must be a string")
    if name in _timezone_cache:
        return _timezone_cache[name]
    tz = Timezone(name)
    _timezone_cache[name] = tz
    return tz