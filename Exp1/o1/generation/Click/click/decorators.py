# click/decorators.py
# Decorators for commands, groups, options, and arguments.

from .core import Command, Group, Option, Argument

def command(name=None, help=None):
    """
    Decorate a function to turn it into a Command.
    """
    def decorator(f):
        return Command(name=name or f.__name__, callback=f, help=help)
    return decorator


def group(name=None, help=None):
    """
    Decorate a function to turn it into a Group.
    """
    def decorator(f):
        grp = Group(name=name or f.__name__, help=help)
        grp.callback = f
        return grp
    return decorator


def option(name, **kwargs):
    """
    Decorate a command function to add an Option parameter.
    """
    def decorator(f):
        if not hasattr(f, "__click_params__"):
            f.__click_params__ = []
        f.__click_params__.append(Option(name, **kwargs))
        return f
    return decorator


def argument(name, **kwargs):
    """
    Decorate a command function to add an Argument parameter.
    """
    def decorator(f):
        if not hasattr(f, "__click_params__"):
            f.__click_params__ = []
        f.__click_params__.append(Argument(name, **kwargs))
        return f
    return decorator