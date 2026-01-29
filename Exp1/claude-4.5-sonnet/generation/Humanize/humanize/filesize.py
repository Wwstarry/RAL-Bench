"""
File size humanization functions.
"""


def naturalsize(value, binary=False, gnu=False, format="%.1f"):
    """
    Format a number of bytes as a human-readable file size.
    
    Args:
        value: Number of bytes
        binary: Use binary (1024) instead of decimal (1000) units
        gnu: Use GNU-style abbreviations (K, M, G instead of KB, MB, GB)
        format: Format string for the number
        
    Returns:
        String like "1.0 MB", "1.5 GB", etc.
    """
    try:
        bytes_val = float(value)
    except (ValueError, TypeError):
        return str(value)
    
    abs_bytes = abs(bytes_val)
    
    if binary:
        base = 1024.0
        if gnu:
            suffixes = ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
        else:
            suffixes = ['Bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']
    else:
        base = 1000.0
        if gnu:
            suffixes = ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
        else:
            suffixes = ['Bytes', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    
    if abs_bytes == 1:
        return '1 Byte' if not gnu else '1'
    
    if abs_bytes < base:
        return '%d Bytes' % int(bytes_val) if not gnu else '%d' % int(bytes_val)
    
    for i, suffix in enumerate(suffixes):
        unit = base ** i
        if abs_bytes < base ** (i + 1):
            value_in_unit = bytes_val / unit
            formatted = format % value_in_unit
            
            if gnu:
                return formatted + suffix
            else:
                if suffix == 'Bytes':
                    return '%d %s' % (int(bytes_val), suffix)
                return formatted + ' ' + suffix
    
    # If we get here, use the largest unit
    value_in_unit = bytes_val / (base ** (len(suffixes) - 1))
    formatted = format % value_in_unit
    
    if gnu:
        return formatted + suffixes[-1]
    else:
        return formatted + ' ' + suffixes[-1]