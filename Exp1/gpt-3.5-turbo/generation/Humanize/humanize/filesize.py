def naturalsize(value, binary=False, format="%.1f %s", gnu=False):
    """
    Return a human-readable file size.

    :param value: size in bytes
    :param binary: use binary (1024) units if True, else decimal (1000)
    :param format: format string for the number and unit
    :param gnu: if True, use GNU style units (KiB, MiB, etc)
    """
    try:
        value = float(value)
    except (TypeError, ValueError):
        return value

    if value < 0:
        return "-" + naturalsize(-value, binary=binary, format=format, gnu=gnu)

    if binary:
        base = 1024
        if gnu:
            units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
        else:
            units = ["bytes", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
    else:
        base = 1000
        units = ["bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]

    if value < base:
        if binary or gnu:
            return "%d %s" % (value, units[0])
        else:
            return "%d %s" % (value, units[0])

    for i, unit in enumerate(units[1:], 1):
        unit_threshold = base ** i
        next_threshold = base ** (i + 1) if i + 1 < len(units) else None
        if next_threshold is None or value < next_threshold:
            return format % (value / unit_threshold, unit)

    # If value is huge, just use the largest unit
    return format % (value / (base ** (len(units) - 1)), units[-1])