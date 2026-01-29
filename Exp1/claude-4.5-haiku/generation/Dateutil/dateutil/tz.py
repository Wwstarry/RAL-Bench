"""
Timezone support for dateutil
"""

from datetime import datetime, timedelta, timezone, tzinfo
from typing import Optional


class tzutc(tzinfo):
    """UTC timezone"""
    
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
    """Fixed offset timezone"""
    
    def __init__(self, name: Optional[str], offset: timedelta):
        """
        Initialize a fixed offset timezone.
        
        Args:
            name: Name of the timezone
            offset: Offset as a timedelta
        """
        self.name = name
        if isinstance(offset, timedelta):
            self._offset = offset
        else:
            # Assume it's seconds
            self._offset = timedelta(seconds=offset)
    
    def utcoffset(self, dt):
        return self._offset
    
    def tzname(self, dt):
        return self.name or "UTC"
    
    def dst(self, dt):
        return timedelta(0)
    
    def __repr__(self):
        return f"tzoffset({self.name!r}, {self._offset!r})"
    
    def __eq__(self, other):
        if isinstance(other, tzoffset):
            return self._offset == other._offset
        return False
    
    def __hash__(self):
        return hash(("tzoffset", self._offset))


# Singleton UTC instance
UTC = tzutc()


def gettz(name: Optional[str] = None) -> Optional[tzinfo]:
    """
    Get a timezone by name.
    
    Args:
        name: Timezone name (e.g., 'UTC', 'US/Eastern', 'Europe/London')
               If None, returns local timezone
    
    Returns:
        tzinfo object or None if timezone not found
    """
    if name is None:
        # Return local timezone
        return None
    
    name_upper = name.upper()
    
    # Handle UTC variants
    if name_upper in ('UTC', 'GMT'):
        return UTC
    
    # Try to parse as fixed offset
    # Format: +HH:MM or -HH:MM
    if name.startswith(('+', '-')):
        try:
            sign = 1 if name[0] == '+' else -1
            parts = name[1:].split(':')
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            offset = timedelta(hours=sign * hours, minutes=sign * minutes)
            return tzoffset(name, offset)
        except (ValueError, IndexError):
            pass
    
    # For now, we don't support named timezones like 'US/Eastern'
    # This would require a timezone database
    return None