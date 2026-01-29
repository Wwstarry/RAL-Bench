"""
Click decorators.
"""

import inspect
from functools import update_wrapper
from .core import Command, Group, Option, Argument, Context


def command(name=None, cls=None, **attrs):
    """Decorator to create a command."""
    if cls is None:
        cls = Command
    
    def decorator(f):
        cmd_name = name or f.__name__.lower().replace('_', '-')
        
        # Extract parameters from function
        params = getattr(f, '__click_params__', [])
        params.reverse()
        
        cmd = cls(name=cmd_name, callback=f, params=params, **attrs)
        cmd.__doc__ = f.__doc__
        return cmd
    
    return decorator


def group(name=None, **attrs):
    """Decorator to create a group."""
    attrs.setdefault('cls', Group)
    return command(name, **attrs)


def option(*param_decls, **attrs):
    """Decorator to add an option."""
    def decorator(f):
        if not hasattr(f, '__click_params__'):
            f.__click_params__ = []
        f.__click_params__.append(Option(param_decls, **attrs))
        return f
    return decorator


def argument(*param_decls, **attrs):
    """Decorator to add an argument."""
    def decorator(f):
        if not hasattr(f, '__click_params__'):
            f.__click_params__ = []
        f.__click_params__.append(Argument(param_decls, **attrs))
        return f
    return decorator


def pass_context(f):
    """Decorator to pass the context as first argument."""
    def wrapper(*args, **kwargs):
        # Find context in args
        ctx = None
        new_args = []
        for arg in args:
            if isinstance(arg, Context):
                ctx = arg
            else:
                new_args.append(arg)
        
        if ctx is None:
            raise RuntimeError("No context available")
        
        return f(ctx, *new_args, **kwargs)
    
    return update_wrapper(wrapper, f)


def pass_obj(f):
    """Decorator to pass the context object."""
    def wrapper(*args, **kwargs):
        ctx = None
        new_args = []
        for arg in args:
            if isinstance(arg, Context):
                ctx = arg
            else:
                new_args.append(arg)
        
        if ctx is None:
            raise RuntimeError("No context available")
        
        return f(ctx.obj, *new_args, **kwargs)
    
    return update_wrapper(wrapper, f)