import sys
import os
import inspect
import functools

# Color codes for secho
_COLOR_CODES = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "white": 37,
    "reset": 39,
}

def _colorize(text, fg=None, bg=None, bold=False, dim=False):
    codes = []
    if fg in _COLOR_CODES:
        codes.append(str(_COLOR_CODES[fg]))
    if bg in _COLOR_CODES:
        codes.append(str(_COLOR_CODES[bg] + 10))
    if bold:
        codes.append("1")
    if dim:
        codes.append("2")
    if codes:
        return "\033[" + ";".join(codes) + "m" + text + "\033[0m"
    return text

def echo(message=None, file=None, nl=True, err=False, color=None):
    """Print a message to stdout or stderr."""
    if file is None:
        file = sys.stderr if err else sys.stdout
    if message is None:
        message = ""
    if nl:
        message = str(message) + "\n"
    else:
        message = str(message)
    if hasattr(file, "write"):
        file.write(message)
        file.flush()

def secho(message=None, file=None, nl=True, err=False, color=None, fg=None, bg=None, bold=False, dim=False):
    """Print a message with color."""
    if message is None:
        message = ""
    colored = _colorize(str(message), fg=fg, bg=bg, bold=bold, dim=dim) if color or fg or bg or bold or dim else str(message)
    echo(colored, file=file, nl=nl, err=err)

class UsageError(Exception):
    pass

class BadParameter(UsageError):
    pass

class MissingParameter(UsageError):
    pass

class Context:
    def __init__(self, command, parent=None, info_name=None, obj=None, params=None):
        self.command = command
        self.parent = parent
        self.info_name = info_name
        self.obj = obj
        self.params = params or {}
        self.invoked_subcommand = None
        self.args = []

    def find_root(self):
        ctx = self
        while ctx.parent is not None:
            ctx = ctx.parent
        return ctx

    def exit(self, code=0):
        raise SystemExit(code)

    def fail(self, message):
        secho(f"Error: {message}", err=True)
        self.exit(1)

    def get_usage(self):
        return self.command.get_usage(self)

    def get_help(self):
        return self.command.get_help(self)

class Parameter:
    def __init__(self, name, param_type_name, opts=None, nargs=1, default=None, required=False, help=None, type=str, prompt=False, is_flag=False, multiple=False, show_default=False, metavar=None):
        self.name = name
        self.param_type_name = param_type_name
        self.opts = opts or []
        self.nargs = nargs
        self.default = default
        self.required = required
        self.help = help
        self.type = type
        self.prompt = prompt
        self.is_flag = is_flag
        self.multiple = multiple
        self.show_default = show_default
        self.metavar = metavar

    def get_display_name(self):
        return self.opts[0] if self.opts else self.name

    def get_metavar(self):
        if self.metavar:
            return self.metavar
        if self.nargs != 1:
            return self.name.upper() + "..."
        return self.name.upper()

    def prompt_for_value(self, ctx):
        prompt_text = self.name.replace("_", " ").capitalize()
        if self.help:
            prompt_text += f" ({self.help})"
        if self.default is not None:
            prompt_text += f" [{self.default}]"
        prompt_text += ": "
        echo(prompt_text, nl=False, err=False)
        value = input()
        if not value and self.default is not None:
            return self.default
        if not value and self.required:
            raise MissingParameter(f"Missing value for '{self.name}'")
        try:
            return self.type(value)
        except Exception:
            raise BadParameter(f"Could not convert '{value}' to {self.type.__name__}")

class Argument(Parameter):
    def __init__(self, name, **kwargs):
        super().__init__(name, param_type_name="argument", **kwargs)

class Option(Parameter):
    def __init__(self, name, opts, **kwargs):
        super().__init__(name, param_type_name="option", opts=opts, **kwargs)

class Command:
    def __init__(self, name=None, callback=None, params=None, help=None, short_help=None, context_settings=None):
        self.name = name
        self.callback = callback
        self.params = params or []
        self.help = help
        self.short_help = short_help
        self.context_settings = context_settings or {}

    def get_usage(self, ctx):
        pieces = [self.name or ctx.info_name or "COMMAND"]
        for param in self.params:
            if param.param_type_name == "option":
                opt = param.opts[0]
                if param.is_flag:
                    pieces.append(f"[{opt}]")
                else:
                    pieces.append(f"[{opt} {param.get_metavar()}]")
            else:
                if param.required:
                    pieces.append(param.get_metavar())
                else:
                    pieces.append(f"[{param.get_metavar()}]")
        return "Usage: " + " ".join(pieces)

    def get_help(self, ctx):
        lines = [self.get_usage(ctx)]
        if self.help:
            lines.append("")
            lines.append(self.help)
        if self.params:
            lines.append("")
            lines.append("Options:")
            for param in self.params:
                opts = ", ".join(param.opts) if param.param_type_name == "option" else param.get_metavar()
                help_text = param.help or ""
                default_text = ""
                if param.show_default and param.default is not None:
                    default_text = f" [default: {param.default}]"
                lines.append(f"  {opts}\t{help_text}{default_text}")
        return "\n".join(lines)

    def invoke(self, ctx):
        args = []
        kwargs = {}
        for param in self.params:
            value = ctx.params.get(param.name, param.default)
            if param.param_type_name == "argument":
                args.append(value)
            else:
                kwargs[param.name] = value
        if self.callback is not None:
            return self.callback(*args, **kwargs)

    def main(self, args=None, prog_name=None, standalone_mode=True, **extra):
        if args is None:
            args = sys.argv[1:]
        ctx = Context(self, info_name=prog_name or self.name)
        try:
            self.parse_args(ctx, args)
            rv = self.invoke(ctx)
            return rv
        except UsageError as e:
            secho(f"Error: {e}", err=True)
            if standalone_mode:
                sys.exit(2)
            raise
        except SystemExit as e:
            if standalone_mode:
                sys.exit(e.code)
            raise
        except Exception as e:
            secho(f"Exception: {e}", err=True)
            if standalone_mode:
                sys.exit(1)
            raise

    def parse_args(self, ctx, args):
        params = {}
        arg_params = [p for p in self.params if p.param_type_name == "argument"]
        opt_params = {opt: p for p in self.params if p.param_type_name == "option" for opt in p.opts}
        i = 0
        consumed_args = []
        # Parse options
        while i < len(args):
            arg = args[i]
            if arg in opt_params:
                param = opt_params[arg]
                if param.is_flag:
                    params[param.name] = True
                    i += 1
                else:
                    if i + 1 >= len(args):
                        raise BadParameter(f"Option {arg} requires a value")
                    value = args[i + 1]
                    try:
                        value = param.type(value)
                    except Exception:
                        raise BadParameter(f"Could not convert '{value}' to {param.type.__name__}")
                    if param.multiple:
                        params.setdefault(param.name, []).append(value)
                    else:
                        params[param.name] = value
                    i += 2
            elif arg == "--help":
                secho(self.get_help(ctx))
                ctx.exit(0)
            elif arg.startswith("-"):
                raise BadParameter(f"Unknown option {arg}")
            else:
                consumed_args.append(arg)
                i += 1
        # Parse arguments
        for idx, param in enumerate(arg_params):
            if idx < len(consumed_args):
                value = consumed_args[idx]
                try:
                    value = param.type(value)
                except Exception:
                    raise BadParameter(f"Could not convert '{value}' to {param.type.__name__}")
                params[param.name] = value
            elif param.prompt:
                params[param.name] = param.prompt_for_value(ctx)
            elif param.required:
                raise MissingParameter(f"Missing argument '{param.name}'")
            else:
                params[param.name] = param.default
        # Set defaults for options
        for param in self.params:
            if param.param_type_name == "option":
                if param.name not in params:
                    if param.is_flag:
                        params[param.name] = False
                    else:
                        params[param.name] = param.default
        ctx.params = params

class Group(Command):
    def __init__(self, name=None, callback=None, params=None, help=None, short_help=None, context_settings=None):
        super().__init__(name, callback, params, help, short_help, context_settings)
        self.commands = {}

    def command(self, *args, **kwargs):
        def decorator(f):
            cmd = Command(name=f.__name__, callback=f, **kwargs)
            self.add_command(cmd)
            return cmd
        return decorator

    def group(self, *args, **kwargs):
        def decorator(f):
            grp = Group(name=f.__name__, callback=f, **kwargs)
            self.add_command(grp)
            return grp
        return decorator

    def add_command(self, cmd, name=None):
        self.commands[name or cmd.name] = cmd

    def get_usage(self, ctx):
        usage = super().get_usage(ctx)
        if self.commands:
            usage += " [COMMAND]"
        return usage

    def get_help(self, ctx):
        lines = [self.get_usage(ctx)]
        if self.help:
            lines.append("")
            lines.append(self.help)
        if self.params:
            lines.append("")
            lines.append("Options:")
            for param in self.params:
                opts = ", ".join(param.opts) if param.param_type_name == "option" else param.get_metavar()
                help_text = param.help or ""
                default_text = ""
                if param.show_default and param.default is not None:
                    default_text = f" [default: {param.default}]"
                lines.append(f"  {opts}\t{help_text}{default_text}")
        if self.commands:
            lines.append("")
            lines.append("Commands:")
            for name, cmd in self.commands.items():
                short = cmd.short_help or (cmd.help.splitlines()[0] if cmd.help else "")
                lines.append(f"  {name}\t{short}")
        return "\n".join(lines)

    def parse_args(self, ctx, args):
        # Parse options for the group itself
        params = {}
        opt_params = {opt: p for p in self.params if p.param_type_name == "option" for opt in p.opts}
        i = 0
        while i < len(args):
            arg = args[i]
            if arg in opt_params:
                param = opt_params[arg]
                if param.is_flag:
                    params[param.name] = True
                    i += 1
                else:
                    if i + 1 >= len(args):
                        raise BadParameter(f"Option {arg} requires a value")
                    value = args[i + 1]
                    try:
                        value = param.type(value)
                    except Exception:
                        raise BadParameter(f"Could not convert '{value}' to {param.type.__name__}")
                    if param.multiple:
                        params.setdefault(param.name, []).append(value)
                    else:
                        params[param.name] = value
                    i += 2
            elif arg == "--help":
                secho(self.get_help(ctx))
                ctx.exit(0)
            elif arg.startswith("-"):
                raise BadParameter(f"Unknown option {arg}")
            else:
                # Assume this is a subcommand
                subcmd_name = arg
                if subcmd_name in self.commands:
                    ctx.params = params
                    ctx.invoked_subcommand = subcmd_name
                    subcmd = self.commands[subcmd_name]
                    sub_ctx = Context(subcmd, parent=ctx, info_name=subcmd_name)
                    subcmd.parse_args(sub_ctx, args[i + 1 :])
                    subcmd.invoke(sub_ctx)
                    ctx.exit(0)
                else:
                    raise UsageError(f"No such command '{subcmd_name}'")
        # No subcommand, just invoke group callback
        ctx.params = params