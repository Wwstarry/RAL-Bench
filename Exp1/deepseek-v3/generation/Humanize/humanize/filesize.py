def naturalsize(value, binary=False, format='%.1f'):
    """Format a number of bytes into a human-readable filesize."""
    if not isinstance(value, (int, float)):
        raise TypeError("naturalsize() argument must be int or float")
    
    if value < 0:
        raise ValueError("naturalsize() argument must be positive")
    
    base = 1024 if binary else 1000
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    
    if value == 0:
        return '0 B'
    
    for suffix in suffixes[:-1]:
        if value < base:
            return f"{format % value} {suffix}"
        value /= base
    
    return f"{format % value} {suffixes[-1]}"