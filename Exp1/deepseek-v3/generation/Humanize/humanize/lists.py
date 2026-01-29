def humanize_list(items, conjunction='and'):
    """Format a list of items into a human-readable string."""
    if not isinstance(items, (list, tuple)):
        raise TypeError("humanize_list() argument must be a list or tuple")
    
    items = [str(item) for item in items]
    
    if not items:
        return ''
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f" {conjunction} ".join(items)
    
    return f"{', '.join(items[:-1])}, {conjunction} {items[-1]}"