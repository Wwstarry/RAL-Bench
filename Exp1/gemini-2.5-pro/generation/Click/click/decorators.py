# -*- coding: utf-8 -*-

import functools
from .core import Command, Group, Option, Argument

def _make_command(f, name, cls, **attrs):
    if name is None:
        name = f.__name__.lower().replace('_', '-')
    
    # Get params attached by decorators, in reverse order of application
    params = getattr(f, '__click_params__', [])
    params.reverse()
    delattr(f, '__click_params__')

    # Add help option automatically
    if attrs.get('add_help_option', True):
        params.append(Option(['--help'], is_flag=True, help='Show this message and exit.'))

    return cls(name=name, callback=f, params=params, **attrs)

def command(name=None, cls=None, **attrs):
    """Creates a new command."""
    if cls is None:
        cls = Command
    
    def decorator(f):
        cmd = _make_command(f, name, cls, **attrs)
        # functools.update_wrapper(cmd, f) # This would copy attributes
        return cmd
    
    return decorator

def group(name=None, **attrs):
    """Creates a new command group."""
    attrs.setdefault('cls', Group)
    return command(name, **attrs)

def _param_decorator(param_cls, *param_decls, **attrs):
    def decorator(f):
        if not hasattr(f, '__click_params__'):
            f.__click_params__ = []
        
        param = param_cls(param_decls, **attrs)
        f.__click_params__.append(param)
        return f
    return decorator

def option(*param_decls, **attrs):
    """Attaches an option to the command."""
    return _param_decorator(Option, *param_decls, **attrs)

def argument(*param_decls, **attrs):
    """Attaches an argument to the command."""
    return _param_decorator(Argument, *param_decls, **attrs)

def pass_context(f):
    """Marks a function as wanting to receive the context object."""
    f.__click_pass_context__ = True
    @functools.wraps(f)
    def new_func(*args, **kwargs):
        return f(*args, **kwargs)
    return new_func

# Helper to be used by _make_command to set pass_context on the command
def _check_for_pass_context(f, attrs):
    if hasattr(f, '__click_pass_context__'):
        attrs['pass_context'] = True

# Monkey-patching _make_command to use the helper
original_make_command = _make_command
def _make_command(f, name, cls, **attrs):
    _check_for_pass_context(f, attrs)
    return original_make_command(f, name, cls, **attrs)