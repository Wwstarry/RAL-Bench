"""
Lunar calculations for moon phase.
"""

import math
from datetime import datetime, date
from typing import Union


def phase(target_date: Union[datetime, date] = None) -> float:
    """
    Calculate the phase of the moon for a given date.
    
    Args:
        target_date: Date for calculation (default: today)
    
    Returns:
        Moon phase as a number between 0 and 27.99 (approximately)
        0 = New Moon
        7 = First Quarter
        14 = Full Moon
        21 = Last Quarter
    """
    if target_date is None:
        target_date = datetime.now().date()
    elif isinstance(target_date, datetime):
        target_date = target_date.date()
    
    # Reference new moon: January 6, 2000
    ref_date = date(2000, 1, 6)
    
    # Calculate days since reference
    days_diff = (target_date - ref_date).days
    
    # Lunar cycle is approximately 29.53058867 days
    lunar_cycle = 29.53058867
    
    # Calculate phase
    phase_value = (days_diff % lunar_cycle) / lunar_cycle * 28.0
    
    return phase_value