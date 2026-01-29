import datetime

class UTC(datetime.timezone):
    def __init__(self):
        super().__init__(datetime.timedelta(0))
    
    def tzname(self, dt):
        return "UTC"
    
    def dst(self, dt):
        return datetime.timedelta(0)
    
    def __repr__(self):
        return "UTC"

# Singleton UTC instance
UTC = UTC()

# Timezone cache
_tz_cache = {}

def gettz(name):
    if name == "UTC":
        return UTC
    
    # Handle fixed offsets
    if name in _tz_cache:
        return _tz_cache[name]
    
    # Parse offset strings
    if name.startswith("GMT") or name.startswith("UTC"):
        offset_str = name[3:]
        if not offset_str:
            return UTC
        
        sign = 1
        if offset_str[0] in ('+', '-'):
            sign = -1 if offset_str[0] == '-' else 1
            offset_str = offset_str[1:]
        
        parts = offset_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1]) if len(parts) > 1 else 0
        offset = sign * (hours * 60 + minutes)
        tz = datetime.timezone(datetime.timedelta(minutes=offset))
        _tz_cache[name] = tz
        return tz
    
    # Return UTC for unknown timezones
    return UTC