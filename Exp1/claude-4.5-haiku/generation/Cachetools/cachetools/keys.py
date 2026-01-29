"""Key generation functions for cache decorators."""

import functools


def hashkey(*args, **kwargs):
    """Generate a cache key from function arguments.
    
    Creates a hashable key from positional and keyword arguments.
    All arguments must be hashable.
    
    Args:
        *args: Positional arguments.
        **kwargs: Keyword arguments.
    
    Returns:
        A hashable key tuple.
    """
    key = args
    if kwargs:
        items = sorted(kwargs.items())
        key = key + (object(),) + tuple(items)
    return key


def methodkey(*args, **kwargs):
    """Generate a cache key for method calls.
    
    Similar to hashkey but skips the first argument (self/cls).
    
    Args:
        *args: Positional arguments (first is self/cls).
        **kwargs: Keyword arguments.
    
    Returns:
        A hashable key tuple.
    """
    # Skip the first argument (self or cls)
    return hashkey(*args[1:], **kwargs)