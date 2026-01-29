from astral.observer import Observer
import datetime

try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Fallback for Python < 3.9 without backports.zoneinfo
    # This is a minimal stub to allow the code to load, though timezone lookups will fail
    class ZoneInfo:
        def __init__(self, key):
            self.key = key
        def utcoffset(self, dt):
            return datetime.timedelta(0)
        def dst(self, dt):
            return datetime.timedelta(0)
        def tzname(self, dt):
            return self.key

class LocationInfo:
    def __init__(self, name='Greenwich', region='England', timezone='UTC', latitude=51.4733, longitude=-0.0008333):
        self.name = name
        self.region = region
        self.timezone = timezone
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self._observer = Observer(self.latitude, self.longitude, 0.0)

    @property
    def observer(self):
        return self._observer

    @property
    def tzinfo(self):
        if not self.timezone or self.timezone.upper() == 'UTC':
            return datetime.timezone.utc
        try:
            return ZoneInfo(self.timezone)
        except Exception:
            return datetime.timezone.utc

    def __repr__(self):
        return f"LocationInfo(name='{self.name}', region='{self.region}', timezone='{self.timezone}', latitude={self.latitude}, longitude={self.longitude})"