# click/decorators.py

import functools
import inspect
from .core import Command, Group, Option, Argument

def _make_command(f, name, cls, **attrs):
    if name is None:
        name = f.__name__.lower().replace("_", "-")
    
    params = getattr(f, "__click_params__", [])
    params.reverse()  # Decorators are applied bottom-up
    
    help_text = attrs.get('help') or inspect.getdoc(f)
    if help_text:
        help_text = inspect.cleandoc(help_text)
    
    attrs['help'] = help_text
    
    cmd = cls(name=name, callback=f, params=params, **attrs)
    
    # Attach the command object to the function, so CliRunner can find it
    f.__click_command__ = cmd
    return f

def command(name=None, cls=None, **attrs):
    """A decorator to create a command from a function."""
    if cls is None:
        cls = Command
    
    def decorator(f):
        return _make_command(f, name, cls, **attrs)
    return decorator

def group(name=None, **attrs):
    """A decorator to create a group of commands."""
    attrs.setdefault("cls", Group)
    return command(name, **attrs)

def _param_decorator(param_cls, param_decls, attrs):
    def decorator(f):
        if not hasattr(f, "__click_params__"):
            f.__click_params__ = []
        f.__click_params__.append(param_cls(param_decls, **attrs))
        return f
    return decorator

def option(*param_decls, **attrs):
    """Adds an option to a command."""
    return _param_decorator(Option, param_decls, attrs)

def argument(*param_decls, **attrs):
    """Adds an argument to a command."""
    return _param_decorator(Argument, param_decls, attrs)

def pass_context(f):
    """Marks a function to receive the context as the first argument."""
    f.__click_pass_context__ = True
    return f