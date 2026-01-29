"""
Utility functions.
"""

import functools


def cached_property(func):
    """Decorator for cached property."""
    attr_name = '_cached_' + func.__name__
    
    @property
    @functools.wraps(func)
    def wrapper(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, func(self))
        return getattr(self, attr_name)
    
    return wrapper


def gen_task_name(app, name, module):
    """Generate task name."""
    if module == '__main__':
        module = None
    if module:
        return f'{module}.{name}'
    return name


def get_full_cls_name(obj):
    """Get full class name."""
    cls = obj if isinstance(obj, type) else type(obj)
    module = cls.__module__
    name = cls.__qualname__
    if module and module != '__builtin__':
        return f'{module}.{name}'
    return name