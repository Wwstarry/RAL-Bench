import re
from pendulum.datetime import DateTime
from pendulum.timezone import Timezone
from pendulum.utils import parse_iso8601

def parse(text, strict=True):
    """Parse a date string into a DateTime object."""
    if isinstance(text, DateTime):
        return text
    
    text = str(text).strip()
    
    iso_result = parse_iso8601(text)
    if iso_result:
        year = iso_result['year']
        month = iso_result['month']
        day = iso_result['day']
        hour = iso_result['hour']
        minute = iso_result['minute']
        second = iso_result['second']
        microsecond = iso_result['microsecond']
        tz = iso_result['tz']
        
        if tz:
            if tz == 'UTC':
                tz_obj = Timezone('UTC')
            else:
                try:
                    tz_obj = Timezone(tz)
                except:
                    tz_obj = Timezone('UTC')
        else:
            tz_obj = None
        
        return DateTime(year, month, day, hour, minute, second, microsecond, tzinfo=tz_obj)
    
    raise ValueError(f"Unable to parse date string: {text}")