import functools
from .core import Command, Group, Option, Argument

def command(name=None, **attrs):
    def decorator(f):
        cmd = Command(name=name or f.__name__, callback=f, **attrs)
        return functools.update_wrapper(cmd, f)
    return decorator

def group(name=None, **attrs):
    def decorator(f):
        grp = Group(name=name or f.__name__, callback=f, **attrs)
        return functools.update_wrapper(grp, f)
    return decorator

def option(*param_decls, **attrs):
    def decorator(f):
        if not hasattr(f, "__click_params__"):
            f.__click_params__ = []
        opts = []
        name = None
        for decl in param_decls:
            if decl.startswith("--"):
                opts.append(decl)
                if not name:
                    name = decl.lstrip("-").replace("-", "_")
            elif decl.startswith("-"):
                opts.append(decl)
            else:
                name = decl.replace("-", "_")
        if not name and opts:
            name = opts[0].lstrip("-").replace("-", "_")
        param = Option(name=name, opts=opts, **attrs)
        f.__click_params__.append(param)
        return f
    return decorator

def argument(param_decls, **attrs):
    def decorator(f):
        if not hasattr(f, "__click_params__"):
            f.__click_params__ = []
        name = param_decls.replace("-", "_")
        param = Argument(name=name, **attrs)
        f.__click_params__.append(param)
        return f
    return decorator

# Patch Command/Group to collect parameters from decorators
def _patch_command_params(cls):
    orig_init = cls.__init__
    def __init__(self, *args, callback=None, params=None, **kwargs):
        if callback and hasattr(callback, "__click_params__"):
            params = list(callback.__click_params__) + (params or [])
        orig_init(self, *args, callback=callback, params=params, **kwargs)
    cls.__init__ = __init__
_patch_command_params(Command)
_patch_command_params(Group)