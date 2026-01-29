def naturalsize(value, binary=False, gnu=False, format="%.1f"):
    """
    Converts a size in bytes to a human-readable string.
    """
    try:
        value = float(value)
    except Exception:
        return str(value)

    if binary:
        prefixes = ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB']
        factor = 1024.0
        suffix = 'bytes'
    else:
        prefixes = ['kB', 'MB', 'GB', 'TB', 'PB', 'EB']
        factor = 1000.0
        suffix = 'bytes'

    if value < factor:
        if gnu:
            return "%dB" % value
        return "%d bytes" % value

    for i, pre in enumerate(prefixes):
        unit = factor ** (i + 1)
        if value < unit * factor:
            val = value / unit
            if gnu:
                # Gnu style: 1K, 1.1M, etc.
                pre_gnu = pre[0]
                if val >= 10:
                    return "%d%s" % (int(val), pre_gnu)
                else:
                    return "%.1f%s" % (val, pre_gnu)
            else:
                return (format + " %s") % (val, pre)
    # If value is huge
    val = value / (factor ** len(prefixes))
    pre = prefixes[-1]
    if gnu:
        pre_gnu = pre[0]
        if val >= 10:
            return "%d%s" % (int(val), pre_gnu)
        else:
            return "%.1f%s" % (val, pre_gnu)
    else:
        return (format + " %s") % (val, pre)