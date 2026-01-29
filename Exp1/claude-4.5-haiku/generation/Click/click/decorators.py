"""
Decorators for Click commands.
"""

import functools
from typing import Any, Callable, List, Optional, Union
from click.core import Command, Group, Option, Argument, Context


def command(
    name: Optional[str] = None,
    **kwargs
) -> Callable:
    """Decorator to create a command."""
    def decorator(f: Callable) -> Command:
        cmd = Command(
            name=name or f.__name__,
            callback=f,
            **kwargs
        )
        return cmd
    return decorator


def group(
    name: Optional[str] = None,
    **kwargs
) -> Callable:
    """Decorator to create a group."""
    def decorator(f: Callable) -> Group:
        grp = Group(
            name=name or f.__name__,
            callback=f,
            **kwargs
        )
        return grp
    return decorator


def option(
    *param_decls: str,
    **kwargs
) -> Callable:
    """Decorator to add an option to a command."""
    def decorator(f: Union[Command, Group, Callable]) -> Union[Command, Group, Callable]:
        if isinstance(f, (Command, Group)):
            # Adding to existing command/group
            opt = Option(list(param_decls), **kwargs)
            f.params.append(opt)
            return f
        else:
            # Wrapping a function
            opt = Option(list(param_decls), **kwargs)
            if not hasattr(f, "__click_params__"):
                f.__click_params__ = []
            f.__click_params__.append(opt)
            return f
    return decorator


def argument(
    *param_decls: str,
    **kwargs
) -> Callable:
    """Decorator to add an argument to a command."""
    def decorator(f: Union[Command, Group, Callable]) -> Union[Command, Group, Callable]:
        if isinstance(f, (Command, Group)):
            # Adding to existing command/group
            arg = Argument(list(param_decls), **kwargs)
            f.params.append(arg)
            return f
        else:
            # Wrapping a function
            arg = Argument(list(param_decls), **kwargs)
            if not hasattr(f, "__click_params__"):
                f.__click_params__ = []
            f.__click_params__.append(arg)
            return f
    return decorator


def pass_context(f: Callable) -> Callable:
    """Decorator to pass the context as the first argument."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    wrapper.__click_pass_context__ = True
    return wrapper