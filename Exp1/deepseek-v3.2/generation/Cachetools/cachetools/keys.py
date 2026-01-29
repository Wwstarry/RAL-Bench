"""
Key functions for cache decorators
"""

import collections.abc
from typing import Any, Hashable


def hashkey(*args: Any, **kwargs: Any) -> Hashable:
    """
    Generate a hash key from function arguments.
    
    Returns:
        Hashable key suitable for use as cache key
    """
    # Handle keyword arguments
    if kwargs:
        # Sort kwargs by key for consistent ordering
        sorted_items = tuple(sorted(kwargs.items()))
        return (args, sorted_items)
    
    # Handle single argument case
    if len(args) == 1:
        arg = args[0]
        # Special handling for common types
        if isinstance(arg, collections.abc.Hashable):
            return arg
        # For non-hashable types, fall back to tuple
        return (arg,)
    
    # Multiple arguments
    return args


def methodkey(method: Any, *args: Any, **kwargs: Any) -> Hashable:
    """
    Generate a hash key for method calls.
    
    Args:
        method: The method object (self for instance methods)
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        Hashable key suitable for use as cache key
    """
    # Include the instance (self) in the key
    return hashkey(method, *args, **kwargs)


# For backward compatibility
_methodkey = methodkey