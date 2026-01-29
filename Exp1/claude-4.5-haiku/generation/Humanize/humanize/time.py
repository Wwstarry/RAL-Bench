"""
Time formatting utilities.
"""

from datetime import datetime, timedelta
from typing import Union, Optional


def naturaldelta(value: Union[int, float, timedelta], months: bool = False, minimum_unit: str = "seconds") -> str:
    """
    Convert a time delta to a human-readable format.
    
    Args:
        value: Time delta in seconds or as a timedelta object
        months: If True, include months in the output
        minimum_unit: Minimum unit to display ("seconds", "minutes", "hours", "days")
    
    Returns:
        Human-readable time delta string
    """
    if isinstance(value, timedelta):
        total_seconds = value.total_seconds()
    else:
        total_seconds = float(value)
    
    # Handle negative values
    if total_seconds < 0:
        return "0 seconds"
    
    # Define time units in seconds
    units = [
        ("year", 365 * 24 * 3600),
        ("month", 30 * 24 * 3600),
        ("week", 7 * 24 * 3600),
        ("day", 24 * 3600),
        ("hour", 3600),
        ("minute", 60),
        ("second", 1),
    ]
    
    # Filter out months if not requested
    if not months:
        units = [u for u in units if u[0] != "month"]
    
    # Find the appropriate unit
    for unit_name, unit_seconds in units:
        if total_seconds >= unit_seconds:
            count = int(total_seconds / unit_seconds)
            unit_display = unit_name if count == 1 else unit_name + "s"
            return f"{count} {unit_display}"
    
    return "0 seconds"


def naturaltime(value: Union[datetime, timedelta], future: bool = False, ago: str = "ago") -> str:
    """
    Convert a datetime or timedelta to a human-readable relative time.
    
    Args:
        value: datetime object or timedelta
        future: If True, format as future time
        ago: String to append for past times (default "ago")
    
    Returns:
        Human-readable relative time string
    """
    if isinstance(value, datetime):
        # Calculate delta from now
        now = datetime.now()
        if value.tzinfo is not None and now.tzinfo is None:
            now = now.replace(tzinfo=value.tzinfo)
        elif value.tzinfo is None and now.tzinfo is not None:
            value = value.replace(tzinfo=now.tzinfo)
        
        delta = now - value
        future = delta.total_seconds() < 0
        delta = abs(delta)
    else:
        delta = value
    
    # Get the natural delta
    delta_str = naturaldelta(delta)
    
    if future:
        return f"{delta_str} from now"
    else:
        return f"{delta_str} {ago}"


def precisedelta(value: Union[datetime, timedelta], minimum_unit: str = "seconds", suppress: list = None) -> str:
    """
    Convert a time delta to a precise human-readable format.
    
    Args:
        value: datetime object or timedelta
        minimum_unit: Minimum unit to display
        suppress: List of units to suppress from output
    
    Returns:
        Precise human-readable time delta string
    """
    if suppress is None:
        suppress = []
    
    if isinstance(value, datetime):
        now = datetime.now()
        if value.tzinfo is not None and now.tzinfo is None:
            now = now.replace(tzinfo=value.tzinfo)
        elif value.tzinfo is None and now.tzinfo is not None:
            value = value.replace(tzinfo=now.tzinfo)
        
        delta = now - value
        total_seconds = abs(delta.total_seconds())
    else:
        total_seconds = abs(value.total_seconds())
    
    # Define time units
    units = [
        ("year", 365 * 24 * 3600),
        ("month", 30 * 24 * 3600),
        ("week", 7 * 24 * 3600),
        ("day", 24 * 3600),
        ("hour", 3600),
        ("minute", 60),
        ("second", 1),
    ]
    
    # Build the result
    parts = []
    remaining = total_seconds
    
    for unit_name, unit_seconds in units:
        if unit_name in suppress:
            continue
        
        if remaining >= unit_seconds:
            count = int(remaining / unit_seconds)
            remaining -= count * unit_seconds
            unit_display = unit_name if count == 1 else unit_name + "s"
            parts.append(f"{count} {unit_display}")
    
    if not parts:
        return "0 seconds"
    
    if len(parts) == 1:
        return parts[0]
    
    # Join with commas and "and"
    return ", ".join(parts[:-1]) + " and " + parts[-1]