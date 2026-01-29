import datetime as _datetime

def format_datetime(dt, fmt, locale='en'):
    """Format a datetime object."""
    return dt.strftime(fmt)