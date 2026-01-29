import datetime
import re
from .tz import gettz, UTC

def parse(timestr, default=None, ignoretz=False, tzinfos=None):
    # Simplified parser that handles common formats
    if default is None:
        default = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Try ISO format first
    try:
        dt = datetime.datetime.fromisoformat(timestr)
        if ignoretz:
            dt = dt.replace(tzinfo=None)
        return dt
    except ValueError:
        pass

    # Handle common non-ISO formats
    patterns = [
        (r"(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})", 6),
        (r"(\d{4})-(\d{2})-(\d{2})", 3),
        (r"(\d{2})/(\d{2})/(\d{4})", 3),
    ]
    
    for pattern, parts in patterns:
        match = re.match(pattern, timestr)
        if match:
            groups = list(map(int, match.groups()))
            if parts == 6:
                dt = datetime.datetime(*groups)
            else:
                dt = datetime.datetime(*groups, default.hour, default.minute, default.second)
            
            if not ignoretz:
                # Attempt to get timezone
                tz_str = timestr[match.end():].strip()
                if tz_str:
                    tz = gettz(tz_str)
                    if tz:
                        dt = dt.replace(tzinfo=tz)
            return dt
    
    # Fallback to now if parsing fails
    return datetime.datetime.now()