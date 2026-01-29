"""
File size formatting utilities.
"""

from typing import Union


def naturalsize(value: Union[int, float], binary: bool = False, gnu: bool = False) -> str:
    """
    Convert a file size in bytes to a human-readable format.
    
    Args:
        value: Size in bytes
        binary: If True, use binary units (1024 bytes = 1 KiB), else decimal (1000 bytes = 1 KB)
        gnu: If True, use GNU-style format (e.g., "1.5G" instead of "1.5 GB")
    
    Returns:
        Human-readable file size string
    """
    value = float(value)
    
    if binary:
        base = 1024
        units = ['bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']
    else:
        base = 1000
        units = ['bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    
    if value == 1:
        return '1 byte'
    elif value < base:
        return f"{int(value)} bytes"
    
    for i, unit in enumerate(units[1:], 1):
        unit_size = base ** i
        if value < base * unit_size:
            size = value / unit_size
            
            # Format with appropriate precision
            if size >= 10:
                formatted = f"{size:.0f}"
            elif size >= 1:
                formatted = f"{size:.1f}"
            else:
                formatted = f"{size:.2f}"
            
            if gnu:
                return f"{formatted}{unit[0]}"
            else:
                return f"{formatted} {unit}"
    
    # Handle very large numbers
    size = value / (base ** (len(units) - 1))
    if size >= 10:
        formatted = f"{size:.0f}"
    elif size >= 1:
        formatted = f"{size:.1f}"
    else:
        formatted = f"{size:.2f}"
    
    unit = units[-1]
    if gnu:
        return f"{formatted}{unit[0]}"
    else:
        return f"{formatted} {unit}"