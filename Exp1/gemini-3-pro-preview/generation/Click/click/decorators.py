import inspect
from .core import Command, Group, Option, Argument

def _param_memo(f, param):
    if not hasattr(f, '__click_params__'):
        f.__click_params__ = []
    f.__click_params__.append(param)

def command(name=None, cls=None, **attrs):
    if cls is None:
        cls = Command
    def decorator(f):
        cmd_name = name or f.__name__.lower().replace('_', '-')
        params = getattr(f, '__click_params__', [])
        # Params are added in reverse order by decorators
        params.reverse()
        cmd = cls(name=cmd_name, callback=f, params=params, **attrs)
        cmd.__doc__ = f.__doc__
        return cmd
    return decorator

def group(name=None, cls=None, **attrs):
    if cls is None:
        cls = Group
    def decorator(f):
        cmd = command(name, cls, **attrs)(f)
        return cmd
    return decorator

def option(*param_decls, **attrs):
    def decorator(f):
        _param_memo(f, Option(param_decls, **attrs))
        return f
    return decorator

def argument(*param_decls, **attrs):
    def decorator(f):
        _param_memo(f, Argument(param_decls, **attrs))
        return f
    return decorator

def pass_context(f):
    def new_func(*args, **kwargs):
        from .core import Context
        # Find context from stack
        ctx = Context._stack[-1]
        return f(ctx, *args, **kwargs)
    return new_func

def pass_obj(f):
    def new_func(*args, **kwargs):
        from .core import Context
        ctx = Context._stack[-1]
        return f(ctx.obj, *args, **kwargs)
    return new_func

def make_pass_decorator(object_type, ensure=False):
    def decorator(f):
        def new_func(*args, **kwargs):
            from .core import Context
            ctx = Context._stack[-1]
            obj = ctx.obj
            if ensure and obj is None:
                obj = object_type()
                ctx.obj = obj
            return f(obj, *args, **kwargs)
        return new_func
    return decorator