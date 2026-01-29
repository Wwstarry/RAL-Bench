"""
Number humanization functions.
"""

import re
from decimal import Decimal


def intcomma(value, ndigits=None):
    """
    Convert an integer to a string containing commas every three digits.
    
    Args:
        value: Integer or string representation of an integer
        ndigits: Number of digits after decimal point (for floats)
    
    Returns:
        String with commas inserted
    """
    try:
        if isinstance(value, str):
            value = value.replace(',', '')
            if '.' in value:
                float_val = float(value)
            else:
                float_val = int(value)
        else:
            float_val = value
            
        if ndigits is not None:
            float_val = round(float(float_val), ndigits)
            
        orig = str(float_val)
        
        if '.' in orig:
            integer_part, decimal_part = orig.split('.')
            negative = integer_part.startswith('-')
            if negative:
                integer_part = integer_part[1:]
            
            # Add commas to integer part
            new_int = ''
            for i, digit in enumerate(reversed(integer_part)):
                if i > 0 and i % 3 == 0:
                    new_int = ',' + new_int
                new_int = digit + new_int
            
            result = new_int + '.' + decimal_part
            if negative:
                result = '-' + result
            return result
        else:
            negative = orig.startswith('-')
            if negative:
                orig = orig[1:]
            
            new = ''
            for i, digit in enumerate(reversed(orig)):
                if i > 0 and i % 3 == 0:
                    new = ',' + new
                new = digit + new
            
            if negative:
                new = '-' + new
            return new
    except (ValueError, TypeError):
        return str(value)


def intword(value, format='%.1f'):
    """
    Convert a large integer to a friendly text representation.
    
    Args:
        value: Integer to convert
        format: Format string for the number part
        
    Returns:
        String representation like "1.0 million"
    """
    try:
        value = int(value)
    except (ValueError, TypeError):
        return str(value)
    
    abs_value = abs(value)
    
    if abs_value < 1000000:
        return intcomma(value)
    
    powers = [
        (10**12, 'trillion'),
        (10**9, 'billion'),
        (10**6, 'million'),
    ]
    
    for power, name in powers:
        if abs_value >= power:
            number = value / float(power)
            return (format % number) + ' ' + name
    
    return intcomma(value)


def ordinal(value):
    """
    Convert an integer to its ordinal as a string.
    
    Args:
        value: Integer to convert
        
    Returns:
        String like "1st", "2nd", "3rd", "4th", etc.
    """
    try:
        value = int(value)
    except (ValueError, TypeError):
        return str(value)
    
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
    
    return str(value) + suffix


def apnumber(value):
    """
    Convert an integer to Associated Press style.
    
    Args:
        value: Integer to convert (0-9 become words, 10+ stay as numbers)
        
    Returns:
        String representation
    """
    try:
        value = int(value)
    except (ValueError, TypeError):
        return str(value)
    
    if 0 <= value <= 9:
        return ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine'][value]
    
    return str(value)


def fractional(value):
    """
    Convert a decimal to a fraction.
    
    Args:
        value: Decimal or float value
        
    Returns:
        String representation as a fraction
    """
    try:
        if isinstance(value, str):
            value = float(value)
        
        # Handle whole numbers
        if value == int(value):
            return str(int(value))
        
        # Common fractions
        fractions = {
            0.25: '1/4',
            0.5: '1/2',
            0.75: '3/4',
            0.333: '1/3',
            0.667: '2/3',
            0.2: '1/5',
            0.4: '2/5',
            0.6: '3/5',
            0.8: '4/5',
        }
        
        decimal_part = value - int(value)
        
        for frac_val, frac_str in fractions.items():
            if abs(decimal_part - frac_val) < 0.01:
                if int(value) == 0:
                    return frac_str
                else:
                    return str(int(value)) + ' ' + frac_str
        
        return str(value)
    except (ValueError, TypeError):
        return str(value)


def scientific(value, precision=2):
    """
    Return number in scientific notation.
    
    Args:
        value: Number to convert
        precision: Number of decimal places
        
    Returns:
        String in scientific notation
    """
    try:
        value = float(value)
        format_str = '%%.%de' % precision
        return format_str % value
    except (ValueError, TypeError):
        return str(value)