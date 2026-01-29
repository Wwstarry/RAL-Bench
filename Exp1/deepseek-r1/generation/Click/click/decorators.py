from .core import Command, Group, Option, Argument

def command(name=None, cls=Command, **attrs):
    if not isinstance(cls, type):
        raise TypeError("cls must be a class, not an instance")
    def decorator(f):
        cmd = cls(name or f.__name__, attrs.get('help', f.__doc__), callback=f, **attrs)
        cmd.params = getattr(f, '__click_params__', [])
        return cmd
    return decorator

def group(name=None, **attrs):
    attrs.setdefault('cls', Group)
    return command(name, **attrs)

def option(*param_decls, **attrs):
    def decorator(f):
        if not hasattr(f, '__click_params__'):
            f.__click_params__ = []
        opt = Option(param_decls, **attrs)
        f.__click_params__.append(opt)
        return f
    return decorator

def argument(*param_decls, **attrs):
    def decorator(f):
        if not hasattr(f, '__click_params__'):
            f.__click_params__ = []
        arg = Argument(param_decls, **attrs)
        f.__click_params__.append(arg)
        return f
    return decorator

def pass_context(f):
    f.__click_pass_context__ = True
    return f

def make_pass_decorator(object_type, ensure=False):
    def decorator(f):
        def new_func(*args, **kwargs):
            ctx = args[0]
            obj = ctx.obj
            if ensure:
                obj = ctx.ensure_object(object_type)
            return ctx.invoke(f, obj, *args[1:], **kwargs)
        return update_wrapper(new_func, f)
    return decorator