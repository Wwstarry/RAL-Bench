import functools
from .core import Command, Group, Option, Argument

def command(name=None, cls=None, **attrs):
    def decorator(f):
        cmd_name = name or f.__name__
        cmd_cls = cls or Command
        cmd = cmd_cls(name=cmd_name, callback=f, **attrs)
        functools.update_wrapper(cmd, f)
        return cmd
    return decorator

def group(name=None, cls=None, **attrs):
    def decorator(f):
        grp_name = name or f.__name__
        grp_cls = cls or Group
        grp = grp_cls(name=grp_name, **attrs)
        f(grp)
        functools.update_wrapper(grp, f)
        return grp
    return decorator

def option(*param_decls, **attrs):
    def decorator(f):
        if not hasattr(f, "__click_params__"):
            f.__click_params__ = []
        opt = Option(param_decls, **attrs)
        f.__click_params__.append(opt)
        return f
    return decorator

def argument(name, **attrs):
    def decorator(f):
        if not hasattr(f, "__click_params__"):
            f.__click_params__ = []
        arg = Argument(name, **attrs)
        f.__click_params__.append(arg)
        return f
    return decorator

# Patch Command and Group to support __click_params__ on decorated functions
def _make_command(f, name=None, cls=None, **attrs):
    cmd_name = name or f.__name__
    cmd_cls = cls or Command
    params = getattr(f, "__click_params__", [])
    cmd = cmd_cls(name=cmd_name, callback=f, params=list(params), **attrs)
    return cmd

def _make_group(f, name=None, cls=None, **attrs):
    grp_name = name or f.__name__
    grp_cls = cls or Group
    grp = grp_cls(name=grp_name, **attrs)
    # Add commands from decorated functions attached to group
    f(grp)
    return grp

# Override decorators to produce Command/Group instances with params
def command(name=None, cls=None, **attrs):
    def decorator(f):
        cmd = _make_command(f, name=name, cls=cls, **attrs)
        functools.update_wrapper(cmd, f)
        return cmd
    return decorator

def group(name=None, cls=None, **attrs):
    def decorator(f):
        grp = _make_group(f, name=name, cls=cls, **attrs)
        functools.update_wrapper(grp, f)
        return grp
    return decorator