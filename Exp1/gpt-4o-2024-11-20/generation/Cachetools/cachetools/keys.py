# Key generation helpers

def hashkey(*args, **kwargs):
    """Generate a hashable key for cache storage."""
    return args + tuple(sorted(kwargs.items()))