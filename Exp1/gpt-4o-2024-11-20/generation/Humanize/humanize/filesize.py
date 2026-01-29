def naturalsize(value, binary=False):
    """
    Convert a file size in bytes to a human-readable format.
    Example: 1024 -> '1.0 KB', 1048576 -> '1.0 MB'
    """
    if not isinstance(value, (int, float)):
        raise ValueError("naturalsize expects an integer or float value.")
    if value < 0:
        raise ValueError("naturalsize expects a non-negative value.")

    base = 1024 if binary else 1000
    suffixes = ["B", "KB", "MB", "GB", "TB", "PB"]
    for suffix in suffixes:
        if value < base:
            return f"{value:.1f} {suffix}"
        value /= base
    return f"{value:.1f} PB"