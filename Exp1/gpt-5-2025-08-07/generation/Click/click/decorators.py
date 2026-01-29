from .core import Command, Group, Option, Argument


def _param_memo(f, param):
    params = getattr(f, "__click_params__", None)
    if params is None:
        params = []
        setattr(f, "__click_params__", params)
    params.append(param)


def command(name=None, help=None, short_help=None, context_settings=None):
    def decorator(f):
        cmd_name = name or f.__name__.replace("_", "-")
        params = getattr(f, "__click_params__", [])[:]
        # Reverse to respect decorator stacking order typical in click
        params.reverse()
        cmd_help = help
        if cmd_help is None and f.__doc__:
            doc = f.__doc__.strip()
            cmd_help = doc
            if short_help is None:
                first = doc.splitlines()[0]
                sh = first.strip()
            else:
                sh = short_help
        else:
            sh = short_help
        cmd = Command(name=cmd_name, params=params, callback=f, help=cmd_help, short_help=sh, context_settings=context_settings or {})
        return cmd

    return decorator


def group(name=None, help=None, short_help=None, context_settings=None):
    def decorator(f):
        grp_name = name or f.__name__.replace("_", "-")
        params = getattr(f, "__click_params__", [])[:]
        params.reverse()
        grp_help = help
        if grp_help is None and f.__doc__:
            doc = f.__doc__.strip()
            grp_help = doc
            if short_help is None:
                first = doc.splitlines()[0]
                sh = first.strip()
            else:
                sh = short_help
        else:
            sh = short_help
        grp = Group(name=grp_name, params=params, callback=f, help=grp_help, short_help=sh, context_settings=context_settings or {})
        return grp

    return decorator


def option(*param_decls, **attrs):
    # attrs includes: help, required, default, type, is_flag, prompt, envvar, nargs, metavar, show_default
    def decorator(f):
        opt = Option(
            param_decls=param_decls,
            required=attrs.get("required", False),
            default=attrs.get("default", None),
            help=attrs.get("help", None),
            type=attrs.get("type", str),
            metavar=attrs.get("metavar", None),
            nargs=attrs.get("nargs", 1),
            envvar=attrs.get("envvar", None),
            expose_value=attrs.get("expose_value", True),
            prompt=attrs.get("prompt", False),
            is_eager=attrs.get("is_eager", False),
            is_flag=attrs.get("is_flag", False) or (attrs.get("flag_value", None) is not None),
            flag_value=attrs.get("flag_value", True),
            show_default=attrs.get("show_default", False),
        )
        _param_memo(f, opt)
        return f

    return decorator


def argument(name, **attrs):
    def decorator(f):
        arg = Argument(
            name=name,
            required=attrs.get("required", True),
            default=attrs.get("default", None),
            type=attrs.get("type", str),
            metavar=attrs.get("metavar", None),
            nargs=attrs.get("nargs", 1),
            envvar=attrs.get("envvar", None),
            expose_value=attrs.get("expose_value", True),
            show_default=attrs.get("show_default", False),
        )
        _param_memo(f, arg)
        return f

    return decorator


def pass_context(f):
    # Mark function to receive ctx as first argument
    setattr(f, "__click_pass_context__", True)
    return f