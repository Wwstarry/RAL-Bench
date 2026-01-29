import datetime
import re

def parse(timestr, default=None, ignoretz=False):
    """
    Parse a string into a datetime object.
    
    Args:
        timestr (str): The string to parse.
        default (datetime.datetime): The default datetime to use for missing fields.
        ignoretz (bool): If True, ignore timezone information in the string.

    Returns:
        datetime.datetime: The parsed datetime object.
    """
    if default is None:
        default = datetime.datetime.now()

    iso_match = re.match(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:Z|([+-]\d{2}:\d{2}))?", timestr)
    if iso_match:
        year, month, day, hour, minute, second, tzinfo = iso_match.groups()
        dt = datetime.datetime(
            int(year), int(month), int(day), int(hour), int(minute), int(second)
        )
        if tzinfo and not ignoretz:
            offset_hours, offset_minutes = map(int, tzinfo.split(":"))
            offset = datetime.timedelta(hours=offset_hours, minutes=offset_minutes)
            dt = dt - offset
        return dt

    raise ValueError(f"Unknown string format: {timestr}")