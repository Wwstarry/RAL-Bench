"""
Number formatting utilities.
"""

import re
from typing import Union


def intcomma(value: Union[int, float, str], ndigits: int = None) -> str:
    """
    Convert an integer to a string containing commas every three digits.
    
    Args:
        value: The number to format
        ndigits: Digits after decimal point (for floats)
    
    Returns:
        String with commas inserted
    """
    if isinstance(value, float):
        if ndigits is not None:
            value = round(value, ndigits)
        str_value = str(value)
    else:
        str_value = str(value)
    
    # Split on decimal point if present
    if '.' in str_value:
        integer_part, decimal_part = str_value.split('.')
    else:
        integer_part = str_value
        decimal_part = None
    
    # Handle negative numbers
    if integer_part.startswith('-'):
        sign = '-'
        integer_part = integer_part[1:]
    else:
        sign = ''
    
    # Add commas to integer part
    integer_part = integer_part[::-1]
    groups = [integer_part[i:i+3] for i in range(0, len(integer_part), 3)]
    integer_part = ','.join(groups)[::-1]
    
    # Reconstruct the number
    result = sign + integer_part
    if decimal_part is not None:
        result += '.' + decimal_part
    
    return result


def ordinal(value: Union[int, str]) -> str:
    """
    Convert an integer to its ordinal representation.
    
    Args:
        value: The number to convert
    
    Returns:
        Ordinal string (e.g., "1st", "2nd", "3rd", "4th")
    """
    value = int(value)
    
    # Special cases for 11, 12, 13
    if value % 100 in (11, 12, 13):
        suffix = 'th'
    else:
        last_digit = value % 10
        if last_digit == 1:
            suffix = 'st'
        elif last_digit == 2:
            suffix = 'nd'
        elif last_digit == 3:
            suffix = 'rd'
        else:
            suffix = 'th'
    
    return f"{value}{suffix}"