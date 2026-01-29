def naturaljoin(value, sep=", ", final_sep=" and "):
    """
    Join a list of strings in a natural way.

    Example:
        naturaljoin(['a', 'b', 'c']) -> 'a, b and c'
    """
    if not value:
        return ""
    if len(value) == 1:
        return str(value[0])
    if len(value) == 2:
        return str(value[0]) + final_sep + str(value[1])
    return sep.join(str(v) for v in value[:-1]) + final_sep + str(value[-1])