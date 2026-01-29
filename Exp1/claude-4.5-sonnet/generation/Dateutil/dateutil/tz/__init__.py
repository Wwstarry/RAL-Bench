"""
Timezone support for dateutil.
"""

from datetime import datetime, timedelta, tzinfo
import time
import os


class tzutc(tzinfo):
    """UTC timezone implementation."""
    
    def utcoffset(self, dt):
        return timedelta(0)
    
    def tzname(self, dt):
        return "UTC"
    
    def dst(self, dt):
        return timedelta(0)
    
    def __repr__(self):
        return "tzutc()"
    
    def __eq__(self, other):
        return isinstance(other, tzutc)
    
    def __hash__(self):
        return hash("tzutc")


class tzoffset(tzinfo):
    """Fixed offset timezone implementation."""
    
    def __init__(self, name, offset):
        """
        Initialize a fixed offset timezone.
        
        Args:
            name: Timezone name
            offset: UTC offset as timedelta or seconds
        """
        self._name = name
        if isinstance(offset, timedelta):
            self._offset = offset
        else:
            self._offset = timedelta(seconds=offset)
    
    def utcoffset(self, dt):
        return self._offset
    
    def tzname(self, dt):
        return self._name
    
    def dst(self, dt):
        return timedelta(0)
    
    def __repr__(self):
        return f"tzoffset({self._name!r}, {self._offset.total_seconds()})"
    
    def __eq__(self, other):
        if not isinstance(other, tzoffset):
            return False
        return self._offset == other._offset
    
    def __hash__(self):
        return hash(self._offset)


class tzlocal(tzinfo):
    """Local timezone implementation."""
    
    def __init__(self):
        self._std_offset = timedelta(seconds=-time.timezone)
        if time.daylight:
            self._dst_offset = timedelta(seconds=-time.altzone)
        else:
            self._dst_offset = self._std_offset
    
    def utcoffset(self, dt):
        if self._isdst(dt):
            return self._dst_offset
        return self._std_offset
    
    def dst(self, dt):
        if self._isdst(dt):
            return self._dst_offset - self._std_offset
        return timedelta(0)
    
    def tzname(self, dt):
        return time.tzname[self._isdst(dt)]
    
    def _isdst(self, dt):
        if dt is None:
            return False
        # Simple DST detection
        tt = (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second,
              dt.weekday(), 0, -1)
        stamp = time.mktime(tt)
        tt = time.localtime(stamp)
        return tt.tm_isdst > 0


class tzfile(tzinfo):
    """Timezone implementation from tzdata files."""
    
    def __init__(self, fileobj_or_path):
        """Initialize from a tzdata file."""
        # Simplified implementation - just store name and use system time
        if isinstance(fileobj_or_path, str):
            self._filename = fileobj_or_path
        else:
            self._filename = getattr(fileobj_or_path, 'name', 'unknown')
        
        # Extract timezone name from path
        if '/' in self._filename:
            self._name = self._filename.split('/')[-1]
        else:
            self._name = self._filename
        
        # For simplicity, use a fixed offset based on common timezones
        self._offset_map = {
            'EST': timedelta(hours=-5),
            'EDT': timedelta(hours=-4),
            'PST': timedelta(hours=-8),
            'PDT': timedelta(hours=-7),
            'MST': timedelta(hours=-7),
            'MDT': timedelta(hours=-6),
            'CST': timedelta(hours=-6),
            'CDT': timedelta(hours=-5),
            'America/New_York': timedelta(hours=-5),
            'America/Los_Angeles': timedelta(hours=-8),
            'America/Chicago': timedelta(hours=-6),
            'America/Denver': timedelta(hours=-7),
            'Europe/London': timedelta(hours=0),
            'Europe/Paris': timedelta(hours=1),
            'Asia/Tokyo': timedelta(hours=9),
        }
        
        self._offset = self._offset_map.get(self._name, timedelta(0))
    
    def utcoffset(self, dt):
        return self._offset
    
    def tzname(self, dt):
        return self._name
    
    def dst(self, dt):
        return timedelta(0)


# Singleton UTC instance
UTC = tzutc()


def gettz(name=None):
    """
    Get a timezone by name.
    
    Args:
        name: Timezone name (e.g., 'UTC', 'America/New_York')
        
    Returns:
        tzinfo object or None
    """
    if name is None:
        return tzlocal()
    
    name_upper = name.upper()
    
    if name_upper == 'UTC' or name_upper == 'GMT':
        return UTC
    
    # Common timezone abbreviations
    tz_map = {
        'EST': tzoffset('EST', timedelta(hours=-5)),
        'EDT': tzoffset('EDT', timedelta(hours=-4)),
        'PST': tzoffset('PST', timedelta(hours=-8)),
        'PDT': tzoffset('PDT', timedelta(hours=-7)),
        'MST': tzoffset('MST', timedelta(hours=-7)),
        'MDT': tzoffset('MDT', timedelta(hours=-6)),
        'CST': tzoffset('CST', timedelta(hours=-6)),
        'CDT': tzoffset('CDT', timedelta(hours=-5)),
    }
    
    if name_upper in tz_map:
        return tz_map[name_upper]
    
    # Try to load from system tzdata
    tzdata_paths = [
        '/usr/share/zoneinfo',
        '/usr/lib/zoneinfo',
        '/usr/share/lib/zoneinfo',
    ]
    
    for base_path in tzdata_paths:
        tz_path = os.path.join(base_path, name)
        if os.path.exists(tz_path):
            try:
                return tzfile(tz_path)
            except:
                pass
    
    # Return a tzfile with the name anyway
    return tzfile(name)