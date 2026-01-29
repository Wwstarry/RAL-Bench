def human_join(seq, delimiter=", ", final=" and "):
    """
    Joins a list into a human-readable string.
    """
    seq = list(seq)
    if not seq:
        return ""
    if len(seq) == 1:
        return str(seq[0])
    return delimiter.join(str(x) for x in seq[:-1]) + final + str(seq[-1])