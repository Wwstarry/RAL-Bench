import datetime as _datetime

class Timezone(_datetime.tzinfo):
    def __init__(self, name, offset=0):
        super().__init__()
        self._name = name
        self._offset = _datetime.timedelta(seconds=offset)

    def utcoffset(self, dt):
        return self._offset

    def tzname(self, dt):
        return self._name

    def dst(self, dt):
        return _datetime.timedelta(0)

def timezone(name):
    if name.upper() == "UTC":
        return Timezone("UTC", 0)
    if name.startswith(('+', '-')):
        sign = 1 if name[0] == '+' else -1
        parts = name[1:].split(':')
        if len(parts) == 2:
            hours = int(parts[0])
            minutes = int(parts[1])
            offset_seconds = sign * (hours * 3600 + minutes * 60)
            return Timezone(name, offset_seconds)
        else:
            hours = int(name[1:])
            offset_seconds = sign * (hours * 3600)
            return Timezone(name, offset_seconds)
    return Timezone(name, 0)