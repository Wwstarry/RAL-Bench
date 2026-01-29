"""
Number humanizing functions.
"""
from typing import Any, Union, Optional

from .i18n import gettext as _, ngettext

__all__ = ["ordinal", "intcomma", "intword", "apnumber", "fractional"]


def ordinal(value: Union[int, str]) -> str:
    """
    Convert an integer to its ordinal as a string.

    1 is '1st', 2 is '2nd', 3 is '3rd', etc.
    
    Args:
        value: The integer to convert
    
    Returns:
        The ordinal string
    """
    try:
        value = int(value)
    except (TypeError, ValueError):
        return str(value)
    
    if value % 100 // 10 != 1:
        if value % 10 == 1:
            ordinal_suffix = _("st")
        elif value % 10 == 2:
            ordinal_suffix = _("nd")
        elif value % 10 == 3:
            ordinal_suffix = _("rd")
        else:
            ordinal_suffix = _("th")
    else:
        ordinal_suffix = _("th")
    
    return f"{value}{ordinal_suffix}"


def intcomma(value: Any, ndigits: Optional[int] = None) -> str:
    """
    Convert an integer to a string containing commas every three digits.
    
    For example, 3000 becomes '3,000' and 45000 becomes '45,000'.
    
    Args:
        value: The value to convert
        ndigits: Number of digits after decimal point
    
    Returns:
        String containing commas every three digits
    """
    try:
        if isinstance(value, str):
            value = float(value)
    except (TypeError, ValueError):
        return str(value)
    
    if ndigits is not None:
        value_str = f"{value:.{ndigits}f}"
    else:
        value_str = str(value)
    
    if '.' in value_str:
        int_part, frac_part = value_str.split('.')
    else:
        int_part, frac_part = value_str, ""
    
    negative = int_part.startswith('-')
    int_part = int_part.lstrip('-')
    
    result = ""
    for i, char in enumerate(reversed(int_part)):
        if i > 0 and i % 3 == 0:
            result = f",{result}"
        result = f"{char}{result}"
    
    if negative:
        result = f"-{result}"
    
    if frac_part:
        result = f"{result}.{frac_part}"
    
    return result


def intword(value: Union[int, float, str]) -> str:
    """
    Convert a large integer to a friendly text representation.
    
    Works best for numbers over 1 million.
    
    Args:
        value: The value to convert
        
    Returns:
        The text representation of the value
    """
    try:
        value = int(value)
    except (TypeError, ValueError):
        return str(value)
    
    abs_value = abs(value)
    
    if abs_value < 1000:
        return str(value)
    
    for exponent, (singular, plural) in enumerate([
        (_("thousand"), _("thousand")),
        (_("million"), _("million")),
        (_("billion"), _("billion")),
        (_("trillion"), _("trillion")),
        (_("quadrillion"), _("quadrillion")),
        (_("quintillion"), _("quintillion")),
        (_("sextillion"), _("sextillion")),
        (_("septillion"), _("septillion")),
        (_("octillion"), _("octillion")),
        (_("nonillion"), _("nonillion")),
        (_("decillion"), _("decillion")),
    ]):
        threshold = 10 ** (3 * (exponent + 1))
        if abs_value < threshold * 1000:
            if value < 0:
                formatted = f"-{abs_value / threshold:.1f}"
            else:
                formatted = f"{abs_value / threshold:.1f}"
                
            # Strip trailing zeros and decimal point if needed
            formatted = formatted.rstrip('0').rstrip('.')
            
            if abs_value >= threshold:
                return _("%(formatted)s %(unit)s") % {
                    "formatted": formatted,
                    "unit": singular if abs_value == threshold else plural,
                }
    
    return str(value)


def apnumber(value: Union[int, str]) -> str:
    """
    For numbers 1-9, returns the number spelled out. Otherwise, returns the number.
    
    Args:
        value: The value to convert
    
    Returns:
        The spelled out number or the number as a string
    """
    try:
        value = int(value)
    except (TypeError, ValueError):
        return str(value)
    
    if 0 < value < 10:
        return {
            1: _("one"),
            2: _("two"),
            3: _("three"),
            4: _("four"),
            5: _("five"),
            6: _("six"),
            7: _("seven"),
            8: _("eight"),
            9: _("nine"),
        }[value]
    
    return str(value)


def fractional(value: Union[float, str]) -> str:
    """
    Convert a float to a human-readable fraction.
    
    Args:
        value: The value to convert
    
    Returns:
        A human-readable fraction representation
    """
    try:
        value = float(value)
    except (TypeError, ValueError):
        return str(value)
    
    whole = int(value)
    frac = abs(value - whole)
    
    if whole and frac:
        return f"{whole} {frac:.2f}".rstrip('0').rstrip('.')
    elif whole:
        return str(whole)
    else:
        return f"{frac:.2f}".rstrip('0').rstrip('.')