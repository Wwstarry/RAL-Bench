import datetime as dt
import pytz

class Timezone:

    def __init__(self, name):
        self._tz = pytz.timezone(name)
        self._name = name

    def __eq__(self, other):
        if not isinstance(other, Timezone):
            return False
        return self._name == other._name

    def __repr__(self):
        return f'Timezone({repr(self._name)})'

    def utcoffset(self, dt):
        return self._tz.utcoffset(dt)

    def dst(self, dt):
        return self._tz.dst(dt)

    def tzname(self, dt):
        return self._tz.tzname(dt)

    def fromutc(self, dt):
        return self._tz.fromutc(dt)

class FixedTimezone(dt.tzinfo):

    def __init__(self, offset, name=None):
        self._offset = dt.timedelta(seconds=offset)
        self._name = name or f'{int(offset / 3600):+03d}:{int((offset % 3600) / 60):02d}'

    def __eq__(self, other):
        if not isinstance(other, FixedTimezone):
            return False
        return self._offset == other._offset

    def __repr__(self):
        return f'FixedTimezone({int(self._offset.total_seconds())}, {repr(self._name)})'

    def utcoffset(self, dt):
        return self._offset

    def dst(self, dt):
        return dt.timedelta(0)

    def tzname(self, dt):
        return self._name