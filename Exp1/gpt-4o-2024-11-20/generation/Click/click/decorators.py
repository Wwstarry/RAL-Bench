# click/decorators.py

from .core import Command, Group


def command(name=None, help=None):
    def decorator(f):
        cmd_name = name or f.__name__
        return Command(name=cmd_name, callback=f, help=help)

    return decorator


def group(name=None, help=None):
    def decorator(f):
        grp_name = name or f.__name__
        return Group(name=grp_name, help=help)

    return decorator


def option(name, **kwargs):
    def decorator(f):
        if not hasattr(f, "__click_params__"):
            f.__click_params__ = []
        f.__click_params__.append((name, kwargs))
        return f

    return decorator


def argument(name, **kwargs):
    def decorator(f):
        if not hasattr(f, "__click_params__"):
            f.__click_params__ = []
        f.__click_params__.append((name, kwargs))
        return f

    return decorator