import datetime as _dt
try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo

class Timezone(zoneinfo.ZoneInfo):
    """
    Pendulum Timezone wrapper around zoneinfo.ZoneInfo.
    """
    def __new__(cls, key):
        if key == "UTC":
            return _dt.timezone.utc
        return super().__new__(cls, key)

    def __repr__(self):
        return f'Timezone("{self.key}")'

    @property
    def name(self):
        return self.key

def fixed_timezone(offset):
    """
    Return a fixed timezone with the given offset (in seconds).
    """
    return _dt.timezone(_dt.timedelta(seconds=offset))