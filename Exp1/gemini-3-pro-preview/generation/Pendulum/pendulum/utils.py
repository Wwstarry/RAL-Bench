import datetime as _dt
import re

def is_leap(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

def days_in_month(year, month):
    if month in [1, 3, 5, 7, 8, 10, 12]:
        return 31
    if month in [4, 6, 9, 11]:
        return 30
    return 29 if is_leap(year) else 28

def parse(text, **options):
    """
    A simplified ISO-8601 parser to satisfy basic API compatibility.
    """
    # Remove Z for UTC and handle manually if necessary, 
    # though fromisoformat handles Z in newer python versions.
    # This is a basic implementation.
    try:
        text = text.replace('Z', '+00:00')
        dt = _dt.datetime.fromisoformat(text)
        
        # Convert to pendulum DateTime
        from .datetime import DateTime
        return DateTime(
            dt.year, dt.month, dt.day,
            dt.hour, dt.minute, dt.second, dt.microsecond,
            tz=dt.tzinfo
        )
    except ValueError:
        raise ValueError(f"Unable to parse string: {text}")

def add_months(dt, months):
    """
    Add months to a datetime, handling end-of-month clamping.
    """
    new_month = dt.month + months
    year_offset = (new_month - 1) // 12
    
    new_year = dt.year + year_offset
    new_month = (new_month - 1) % 12 + 1
    
    new_day = min(dt.day, days_in_month(new_year, new_month))
    
    return dt.replace(year=new_year, month=new_month, day=new_day)