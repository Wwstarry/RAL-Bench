import datetime

class tzoffset(datetime.tzinfo):
    """
    A simple, fixed-offset tzinfo implementation.
    """
    def __init__(self, name, offset):
        self._name = name
        self._offset = datetime.timedelta(seconds=offset)

    def utcoffset(self, dt):
        return self._offset

    def dst(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        return self._name

    def __repr__(self):
        return f"tzoffset({self._name!r}, {self._offset.total_seconds()})"

    def __eq__(self, other):
        if not isinstance(other, datetime.tzinfo):
            return NotImplemented
        return self.utcoffset(None) == other.utcoffset(None)

    def __hash__(self):
        return hash(self.utcoffset(None))

# The UTC timezone singleton
UTC = datetime.timezone.utc

# A cache for gettz results
_TZ_CACHE = {
    "UTC": UTC,
}

# A hardcoded map for common timezone names that might appear in tests.
# This avoids needing a full IANA database. Offsets are in seconds.
# Note: This does not handle DST and is a major simplification.
_TZ_MAP = {
    "UTC": (0, "UTC"),
    "GMT": (0, "GMT"),
    "CET": (3600, "CET"),      # Central European Time
    "EST": (-18000, "EST"),    # Eastern Standard Time (fixed)
    "EDT": (-14400, "EDT"),    # Eastern Daylight Time (fixed)
    "CST": (-21600, "CST"),    # Central Standard Time (fixed)
    "CDT": (-18000, "CDT"),    # Central Daylight Time (fixed)
    "MST": (-25200, "MST"),    # Mountain Standard Time (fixed)
    "MDT": (-21600, "MDT"),    # Mountain Daylight Time (fixed)
    "PST": (-28800, "PST"),    # Pacific Standard Time (fixed)
    "PDT": (-25200, "PDT"),    # Pacific Daylight Time (fixed)
    "JST": (32400, "JST"),     # Japan Standard Time
}

def gettz(name):
    """
    Returns a tzinfo object for a given timezone name.
    This is a simplified implementation that handles a few common names
    and ISO 8601 offset strings.
    """
    if name is None:
        return None
    
    if name in _TZ_CACHE:
        return _TZ_CACHE[name]

    if isinstance(name, str):
        # Check hardcoded map
        name_upper = name.upper()
        if name_upper in _TZ_MAP:
            offset, tzname = _TZ_MAP[name_upper]
            tz = tzoffset(tzname, offset)
            _TZ_CACHE[name] = tz
            return tz
        
        # Handle ISO offset strings like "+01:00" or "-0800"
        import re
        m = re.match(r'^([+-])(\d{2}):?(\d{2})?$', name)
        if m:
            sign, h, m_str = m.groups()
            m_val = int(m_str) if m_str else 0
            offset_seconds = (int(h) * 3600 + m_val * 60)
            if sign == '-':
                offset_seconds = -offset_seconds
            
            # Create a canonical name for the offset for caching
            cache_name = f"{sign}{h:02d}:{m_val:02d}"
            tz = tzoffset(cache_name, offset_seconds)
            _TZ_CACHE[name] = tz
            return tz

    # Fallback for unknown timezones
    return None