import datetime as _datetime
import pytz

class Timezone(_datetime.tzinfo):
    """A Timezone class wrapping pytz timezones."""
    
    def __init__(self, name):
        self.name = name
        try:
            self._tz = pytz.timezone(name)
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Unknown timezone: {name}")
    
    def tzname(self, dt):
        """Get the timezone name."""
        if dt is None:
            return self.name
        return self._tz.tzname(dt)
    
    def utcoffset(self, dt):
        """Get the UTC offset."""
        if dt is None:
            return _datetime.timedelta(0)
        return self._tz.utcoffset(dt)
    
    def dst(self, dt):
        """Get the daylight saving time offset."""
        if dt is None:
            return _datetime.timedelta(0)
        return self._tz.dst(dt)
    
    def localize(self, dt):
        """Localize a naive datetime to this timezone."""
        if dt.tzinfo is not None:
            raise ValueError("Cannot localize aware datetime")
        return self._tz.localize(dt)
    
    def normalize(self, dt):
        """Normalize a datetime in this timezone."""
        return self._tz.normalize(dt)
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f"Timezone('{self.name}')"
    
    def __eq__(self, other):
        if isinstance(other, Timezone):
            return self.name == other.name
        return False
    
    def __hash__(self):
        return hash(self.name)