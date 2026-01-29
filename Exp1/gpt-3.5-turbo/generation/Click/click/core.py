import sys
import os
import functools
import shlex
import inspect
import collections

# Exceptions
class ClickException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def show(self, file=None):
        if file is None:
            file = sys.stderr
        print(f"Error: {self.message}", file=file)

class UsageError(ClickException):
    pass

class Exit(Exception):
    def __init__(self, code=0):
        self.exit_code = code

# Parameter types
class ParamType:
    name = None

    def convert(self, value, param=None, ctx=None):
        return value

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name}>"

class StringParamType(ParamType):
    name = "string"

    def convert(self, value, param=None, ctx=None):
        if value is None:
            return None
        return str(value)

class IntParamType(ParamType):
    name = "int"

    def convert(self, value, param=None, ctx=None):
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            raise UsageError(f"Invalid value for {param.name}: {value!r} is not a valid integer")

class BoolParamType(ParamType):
    name = "bool"

    def convert(self, value, param=None, ctx=None):
        if isinstance(value, bool):
            return value
        val = str(value).lower()
        if val in ("1", "true", "yes", "y", "on"):
            return True
        if val in ("0", "false", "no", "n", "off"):
            return False
        raise UsageError(f"Invalid value for {param.name}: {value!r} is not a valid boolean")

# Global param types
STRING = StringParamType()
INT = IntParamType()
BOOL = BoolParamType()

# Parameter classes
class Parameter:
    def __init__(
        self,
        name,
        param_decls=None,
        type=None,
        required=False,
        default=None,
        help=None,
        is_flag=False,
        flag_value=None,
        multiple=False,
        prompt=False,
        nargs=1,
        metavar=None,
        show_default=False,
        envvar=None,
        expose_value=True,
        callback=None,
    ):
        self.name = name
        self.param_decls = param_decls or []
        self.type = type or STRING
        self.required = required
        self.default = default
        self.help = help
        self.is_flag = is_flag
        self.flag_value = flag_value
        self.multiple = multiple
        self.prompt = prompt
        self.nargs = nargs
        self.metavar = metavar
        self.show_default = show_default
        self.envvar = envvar
        self.expose_value = expose_value
        self.callback = callback

    def get_default(self, ctx):
        if callable(self.default):
            return self.default()
        return self.default

    def _get_envvar_value(self, ctx):
        if self.envvar is None:
            return None
        if isinstance(self.envvar, (tuple, list)):
            for var in self.envvar:
                val = os.environ.get(var)
                if val is not None:
                    return val
            return None
        else:
            return os.environ.get(self.envvar)

    def prompt_for_value(self, ctx):
        if not self.prompt:
            return None
        prompt_text = self.prompt if isinstance(self.prompt, str) else f"Enter {self.name}"
        while True:
            try:
                value = input(f"{prompt_text}: ")
            except EOFError:
                raise UsageError("Input aborted.")
            if value == "" and self.required:
                print("Error: This parameter is required.")
                continue
            if value == "":
                return self.get_default(ctx)
            try:
                return self.type.convert(value, self, ctx)
            except UsageError as e:
                print(e.message)
                continue

    def _consume_value(self, args):
        if self.nargs == 1:
            if not args:
                return None
            return args.pop(0)
        else:
            if len(args) < self.nargs:
                raise UsageError(f"Missing {self.nargs} arguments for {self.name}")
            values = args[: self.nargs]
            del args[: self.nargs]
            return values

    def handle_parse_result(self, ctx, opts, args):
        # opts is dict of option values, args is list of leftover args
        if self.is_flag:
            # flags are boolean options
            value = opts.get(self.name)
            if value is None:
                value = self.get_default(ctx)
            return value
        else:
            # positional or option with value
            if self.name in opts:
                value = opts[self.name]
            else:
                value = None
            if value is None and self.envvar:
                envval = self._get_envvar_value(ctx)
                if envval is not None:
                    try:
                        value = self.type.convert(envval, self, ctx)
                    except UsageError:
                        pass
            if value is None and self.prompt:
                value = self.prompt_for_value(ctx)
            if value is None:
                value = self.get_default(ctx)
            if value is None and self.required:
                raise UsageError(f"Missing parameter {self.name}")
            if self.multiple:
                if value is None:
                    value = ()
                elif not isinstance(value, (tuple, list)):
                    value = (value,)
                else:
                    value = tuple(value)
            else:
                if isinstance(value, (tuple, list)):
                    if len(value) == 1:
                        value = value[0]
                    elif len(value) == 0:
                        value = None
                    else:
                        raise UsageError(f"Got multiple values for parameter {self.name} but multiple=False")
            if self.callback:
                value = self.callback(ctx, self, value)
            return value

class Option(Parameter):
    def __init__(
        self,
        param_decls,
        **attrs,
    ):
        # param_decls is list of option strings like ['-f', '--foo']
        super().__init__(name=None, param_decls=param_decls, **attrs)
        self.name = self._infer_name()

    def _infer_name(self):
        # Infer name from param_decls, prefer long option without dashes
        for decl in self.param_decls:
            if decl.startswith("--"):
                return decl.lstrip("-").replace("-", "_")
        # fallback to first decl without dashes
        return self.param_decls[0].lstrip("-").replace("-", "_")

    def add_to_parser(self, parser):
        # parser is a dict mapping option strings to Option instances
        for decl in self.param_decls:
            parser[decl] = self

class Argument(Parameter):
    def __init__(self, name, **attrs):
        super().__init__(name=name, **attrs)

# Context class
class Context:
    def __init__(self, command, parent=None, info_name=None, obj=None):
        self.command = command
        self.parent = parent
        self.info_name = info_name
        self.obj = obj
        self.params = {}
        self.args = []
        self.invoked_subcommand = None
        self._exit_stack = []

    def invoke(self, command, args=None):
        args = args or []
        ctx = Context(command, parent=self, info_name=command.name, obj=self.obj)
        return command.invoke(ctx, args)

    def forward(self, command, args=None):
        # Like invoke but does not create new context
        args = args or []
        return command.invoke(self, args)

    def exit(self, code=0):
        raise Exit(code)

    def fail(self, message):
        raise UsageError(message)

    def call_on_close(self):
        while self._exit_stack:
            func = self._exit_stack.pop()
            func()

    def push(self, func):
        self._exit_stack.append(func)

# Command class
class Command:
    def __init__(
        self,
        name=None,
        callback=None,
        params=None,
        help=None,
        epilog=None,
        short_help=None,
        options_metavar="[OPTIONS]",
        add_help_option=True,
        no_args_is_help=False,
    ):
        self.name = name
        self.callback = callback
        self.params = params or []
        self.help = help
        self.epilog = epilog
        self.short_help = short_help
        self.options_metavar = options_metavar
        self.add_help_option = add_help_option
        self.no_args_is_help = no_args_is_help

        if self.add_help_option:
            self.params.append(
                Option(
                    ["-h", "--help"],
                    is_flag=True,
                    help="Show this message and exit.",
                    expose_value=False,
                    callback=self._handle_help,
                )
            )

    def _handle_help(self, ctx, param, value):
        if not value or ctx.resilient_parsing:
            return
        self.format_help(ctx, ctx.stdout)
        ctx.exit()

    def get_usage(self, ctx):
        pieces = [self.name or ""]

        opts = []
        args = []

        for param in self.get_params(ctx):
            if isinstance(param, Option):
                opts.append(param)
            else:
                args.append(param)

        if opts:
            pieces.append(self.options_metavar)

        for arg in args:
            if arg.required:
                pieces.append(f"<{arg.name}>")
            else:
                pieces.append(f"[{arg.name}]")

        return " ".join(pieces)

    def get_params(self, ctx):
        return self.params

    def parse_args(self, ctx, args):
        # Returns (opts, args)
        opts = {}
        positionals = []
        # Build option map
        option_map = {}
        for param in self.params:
            if isinstance(param, Option):
                for decl in param.param_decls:
                    option_map[decl] = param

        # Parse args
        iter_args = iter(args)
        while True:
            try:
                arg = next(iter_args)
            except StopIteration:
                break
            if arg == "--":
                # All remaining are positional
                positionals.extend(iter_args)
                break
            if arg.startswith("--"):
                # Long option
                if "=" in arg:
                    opt, val = arg.split("=", 1)
                else:
                    opt = arg
                    val = None
                param = option_map.get(opt)
                if param is None:
                    raise UsageError(f"Unknown option: {opt}")
                if param.is_flag:
                    opts[param.name] = param.flag_value if param.flag_value is not None else True
                else:
                    if val is None:
                        try:
                            val = next(iter_args)
                        except StopIteration:
                            raise UsageError(f"Option {opt} requires a value")
                    opts[param.name] = val
            elif arg.startswith("-") and arg != "-":
                # Short option(s)
                # Could be combined like -abc
                shorts = arg[1:]
                while shorts:
                    opt = "-" + shorts[0]
                    shorts = shorts[1:]
                    param = option_map.get(opt)
                    if param is None:
                        raise UsageError(f"Unknown option: {opt}")
                    if param.is_flag:
                        opts[param.name] = param.flag_value if param.flag_value is not None else True
                    else:
                        if shorts:
                            val = shorts
                            shorts = ""
                        else:
                            try:
                                val = next(iter_args)
                            except StopIteration:
                                raise UsageError(f"Option {opt} requires a value")
                        opts[param.name] = val
                        break
            else:
                # Positional argument
                positionals.append(arg)

        return opts, positionals

    def invoke(self, ctx, args):
        try:
            opts, args = self.parse_args(ctx, args)
            # Parse parameters
            params = {}
            for param in self.params:
                if isinstance(param, Option):
                    value = param.handle_parse_result(ctx, opts, args)
                else:
                    # Argument
                    # Consume from args
                    if param.multiple:
                        value = tuple(args)
                        args.clear()
                    else:
                        if args:
                            value = args.pop(0)
                        else:
                            value = None
                    if value is not None:
                        try:
                            value = param.type.convert(value, param, ctx)
                        except UsageError as e:
                            raise UsageError(f"Invalid value for {param.name}: {e.message}")
                    if value is None and param.required:
                        raise UsageError(f"Missing argument {param.name}")
                    if param.callback:
                        value = param.callback(ctx, param, value)
                if param.expose_value:
                    params[param.name] = value

            ctx.params = params
            ctx.args = args

            if self.no_args_is_help and not args and not opts:
                self.format_help(ctx, ctx.stdout)
                ctx.exit()

            rv = self.callback(**params)
            if rv is None:
                return 0
            if isinstance(rv, int):
                return rv
            return 0
        except Exit as e:
            return e.exit_code
        except UsageError as e:
            e.show()
            return 2

    def format_help(self, ctx, file=None):
        if file is None:
            file = sys.stdout
        usage = self.get_usage(ctx)
        print(f"Usage: {usage}", file=file)
        if self.help:
            print()
            print(self.help, file=file)
        if self.params:
            print()
            print("Options:", file=file)
            for param in self.params:
                if param.is_flag:
                    opts = ", ".join(param.param_decls)
                    help_text = param.help or ""
                    print(f"  {opts}\t{help_text}", file=file)
                elif isinstance(param, Option):
                    opts = ", ".join(param.param_decls) + f" <{param.name}>"
                    help_text = param.help or ""
                    print(f"  {opts}\t{help_text}", file=file)
            # Arguments
            args = [p for p in self.params if not isinstance(p, Option)]
            if args:
                print()
                print("Arguments:", file=file)
                for arg in args:
                    help_text = arg.help or ""
                    print(f"  {arg.name}\t{help_text}", file=file)

class Group(Command):
    def __init__(self, name=None, commands=None, **attrs):
        super().__init__(name=name, **attrs)
        self.commands = commands or {}

    def command(self, *args, **kwargs):
        def decorator(f):
            cmd = Command(*args, callback=f, **kwargs)
            self.add_command(cmd)
            return cmd

        return decorator

    def group(self, *args, **kwargs):
        def decorator(f):
            grp = Group(*args, **kwargs)
            self.add_command(grp)
            f(grp)
            return grp

        return decorator

    def add_command(self, cmd):
        if cmd.name is None:
            raise TypeError("Commands must have a name.")
        self.commands[cmd.name] = cmd

    def get_command(self, ctx, cmd_name):
        return self.commands.get(cmd_name)

    def list_commands(self, ctx):
        return sorted(self.commands.keys())

    def invoke(self, ctx, args):
        try:
            opts, args = self.parse_args(ctx, args)
            # Parse options for group itself
            params = {}
            for param in self.params:
                if isinstance(param, Option):
                    value = param.handle_parse_result(ctx, opts, args)
                    if param.expose_value:
                        params[param.name] = value
            ctx.params = params
            ctx.args = args

            if not args:
                if self.no_args_is_help:
                    self.format_help(ctx, ctx.stdout)
                    ctx.exit()
                else:
                    # No subcommand given
                    self.format_help(ctx, ctx.stdout)
                    ctx.exit(2)

            cmd_name = args.pop(0)
            cmd = self.get_command(ctx, cmd_name)
            if cmd is None:
                raise UsageError(f"No such command '{cmd_name}'.")

            ctx.invoked_subcommand = cmd
            return cmd.invoke(ctx, args)
        except Exit as e:
            return e.exit_code
        except UsageError as e:
            e.show()
            return 2

# Output functions
def echo(message=None, file=None, nl=True, err=False, color=None, **styles):
    if file is None:
        file = sys.stderr if err else sys.stdout
    if message is None:
        out = ""
    else:
        out = str(message)
    if color or styles:
        out = _ansi_wrap(out, color, **styles)
    if nl:
        print(out, file=file)
    else:
        print(out, file=file, end="")
    file.flush()

def secho(message=None, file=None, nl=True, err=False, fg=None, bg=None, bold=False, dim=False, underline=False, blink=False, reverse=False, reset=True):
    # fg and bg are colors
    if file is None:
        file = sys.stderr if err else sys.stdout
    if message is None:
        out = ""
    else:
        out = str(message)
    out = _ansi_wrap(out, fg, bg=bg, bold=bold, dim=dim, underline=underline, blink=blink, reverse=reverse, reset=reset)
    if nl:
        print(out, file=file)
    else:
        print(out, file=file, end="")
    file.flush()

def _ansi_wrap(text, fg=None, bg=None, bold=False, dim=False, underline=False, blink=False, reverse=False, reset=True, **kwargs):
    # ANSI color codes
    COLORS = {
        "black": 0,
        "red": 1,
        "green": 2,
        "yellow": 3,
        "blue": 4,
        "magenta": 5,
        "cyan": 6,
        "white": 7,
        "bright_black": 8,
        "bright_red": 9,
        "bright_green": 10,
        "bright_yellow": 11,
        "bright_blue": 12,
        "bright_magenta": 13,
        "bright_cyan": 14,
        "bright_white": 15,
    }

    def code(n):
        return f"\033[{n}m"

    seq = []

    if fg is not None:
        fg_code = COLORS.get(fg.lower(), None)
        if fg_code is not None:
            if fg_code < 8:
                seq.append(code(30 + fg_code))
            else:
                seq.append(code(90 + fg_code - 8))
    if bg is not None:
        bg_code = COLORS.get(bg.lower(), None)
        if bg_code is not None:
            if bg_code < 8:
                seq.append(code(40 + bg_code))
            else:
                seq.append(code(100 + bg_code - 8))
    if bold:
        seq.append(code(1))
    if dim:
        seq.append(code(2))
    if underline:
        seq.append(code(4))
    if blink:
        seq.append(code(5))
    if reverse:
        seq.append(code(7))

    start = "".join(seq)
    end = code(0) if reset else ""

    return f"{start}{text}{end}"