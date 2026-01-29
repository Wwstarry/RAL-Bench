"""
filesize.py

Human-readable file size formatting.
"""

def naturalsize(value, binary=False, gnu=False, format="%.1f"):
    """
    Format a number of bytes like a human readable filesize (e.g. '10 kB').
    If binary is True, use powers of 1024 instead of 1000 (KiB, MiB, etc).
    If gnu is True, use 'K', 'M', ... without the 'iB' suffix for binary sizes.
    """
    try:
        bytes_float = float(value)
    except:
        return str(value)

    abs_bytes = abs(bytes_float)

    if abs_bytes < 1:
        return "%d Bytes" % bytes_float

    if binary:
        prefixes = [
            (1 << 50, 'PiB', 'P'),
            (1 << 40, 'TiB', 'T'),
            (1 << 30, 'GiB', 'G'),
            (1 << 20, 'MiB', 'M'),
            (1 << 10, 'KiB', 'K'),
            (1, 'Byte', 'B')
        ]
    else:
        prefixes = [
            (1e15, 'PB', 'P'),
            (1e12, 'TB', 'T'),
            (1e9, 'GB', 'G'),
            (1e6, 'MB', 'M'),
            (1e3, 'kB', 'K'),
            (1, 'Bytes', 'B')
        ]

    for factor, suffix, gnu_suffix in prefixes:
        if abs_bytes >= factor:
            val = bytes_float / factor
            if gnu:
                return (format % val) + gnu_suffix
            # singular/plural
            if factor == 1:
                return "%d Byte%s" % (bytes_float, "s" if bytes_float != 1 else "")
            return (format % val) + " " + suffix

    # fallback
    return str(value)