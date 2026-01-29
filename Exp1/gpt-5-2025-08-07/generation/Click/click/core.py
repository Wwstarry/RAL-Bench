import sys
import os
import shlex

# Exceptions


class ClickException(Exception):
    exit_code = 1

    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def format_message(self):
        return self.message

    def show(self, file=None):
        if file is None:
            file = sys.stderr
        echo = getattr(sys.modules.get("click.termui", None) or __import__("click.termui", fromlist=["echo"]), "echo")
        echo(f"Error: {self.format_message()}", file=file, err=True)


class UsageError(ClickException):
    exit_code = 2

    def __init__(self, message, ctx=None):
        super().__init__(message)
        self.ctx = ctx

    def show(self, file=None):
        if file is None:
            file = sys.stderr
        termui = sys.modules.get("click.termui", None) or __import__("click.termui", fromlist=["echo"])
        echo = getattr(termui, "echo")
        # Show error
        echo(f"Error: {self.format_message()}", file=file, err=True)
        # Try suggestion line with program name
        prog = None
        if self.ctx is not None:
            prog = self.ctx.command_path
        if not prog:
            prog = "command"
        echo(f"Try '{prog} --help' for help.", file=file, err=True)


class BadParameter(UsageError):
    pass


class MissingParameter(UsageError):
    pass


# Context


class Context:
    def __init__(self, command, parent=None, info_name=None, obj=None):
        self.command = command
        self.parent = parent
        self.info_name = info_name
        self.obj = obj
        self.params = {}
        self.default_map = None

    @property
    def command_path(self):
        parts = []
        ctx = self
        while ctx is not None:
            if ctx.info_name:
                parts.append(ctx.info_name)
            ctx = ctx.parent
        return " ".join(reversed(parts)).strip()

    def find_root(self):
        c = self
        while c.parent is not None:
            c = c.parent
        return c

    def get_help(self):
        return self.command.get_help(self)


# Parameters


class Parameter:
    param_type_name = "parameter"

    def __init__(
        self,
        name=None,
        required=False,
        default=None,
        help=None,
        type=str,
        metavar=None,
        nargs=1,
        envvar=None,
        expose_value=True,
        prompt=False,
        is_eager=False,
        show_default=False,
    ):
        self.name = name
        self.required = required
        self.default = default
        self.help = help
        self.type = type
        self.metavar = metavar
        self.nargs = nargs
        self.envvar = envvar
        self.expose_value = expose_value
        self.prompt = prompt
        self.is_eager = is_eager
        self.show_default = show_default

    def get_default(self, ctx):
        if self.envvar:
            val = os.environ.get(self.envvar)
            if val is not None and val != "":
                try:
                    return self.convert(val, ctx)
                except Exception:
                    pass
        return self.default

    def convert(self, value, ctx):
        if self.type is None or value is None:
            return value
        if self.type is bool:
            # Accept "true"/"false"
            if isinstance(value, str):
                v = value.strip().lower()
                if v in ("1", "true", "t", "yes", "y", "on"):
                    return True
                if v in ("0", "false", "f", "no", "n", "off"):
                    return False
            return bool(value)
        try:
            return self.type(value)
        except Exception as e:
            pname = self.name.upper() if isinstance(self, Argument) else f"--{self.name.replace('_','-')}"
            raise BadParameter(f"Invalid value for '{pname}': {e}", ctx=ctx)

    def process_value(self, values, ctx):
        # values is a list of tokens to consume based on nargs
        if self.nargs == -1:
            items = values[:]
            return [self.convert(v, ctx) for v in items], []
        elif self.nargs == 0:
            return None, values
        else:
            if len(values) < self.nargs:
                self.fail_missing(ctx)
            items = values[: self.nargs]
            rest = values[self.nargs :]
            if self.nargs == 1:
                return self.convert(items[0], ctx), rest
            else:
                return [self.convert(v, ctx) for v in items], rest

    def fail_missing(self, ctx):
        if isinstance(self, Argument):
            raise MissingParameter(f"Missing argument '{self.name.upper()}'.", ctx=ctx)
        else:
            raise MissingParameter(f"Missing option '--{self.name.replace('_','-')}'.", ctx=ctx)

    def get_help_record(self, ctx):
        return None


class Option(Parameter):
    param_type_name = "option"

    def __init__(
        self,
        param_decls,
        required=False,
        default=None,
        help=None,
        type=str,
        metavar=None,
        nargs=1,
        envvar=None,
        expose_value=True,
        prompt=False,
        is_eager=False,
        is_flag=False,
        flag_value=True,
        show_default=False,
    ):
        # param_decls: tuple of option strings like ('-f', '--foo')
        super().__init__(
            name=None,
            required=required,
            default=default,
            help=help,
            type=(bool if is_flag and type is str else type),
            metavar=metavar,
            nargs=(0 if is_flag else nargs),
            envvar=envvar,
            expose_value=expose_value,
            prompt=prompt,
            is_eager=is_eager,
            show_default=show_default,
        )
        self.opts = tuple(param_decls)
        self.secondary_opts = ()
        self.is_flag = is_flag
        self.flag_value = flag_value
        # derive name from last long option or first
        name = None
        for o in self.opts:
            if o.startswith("--"):
                name = o.lstrip("-").replace("-", "_")
                break
        if name is None and self.opts:
            name = self.opts[-1].lstrip("-")
        self.name = name or "param"

    def takes_value(self):
        return not self.is_flag

    def get_help_record(self, ctx):
        # generate option metastr
        parts = []
        if self.opts:
            parts.append(", ".join(self.opts))
        if self.takes_value():
            meta = self.metavar or self.name.upper()
            parts[-1] = f"{parts[-1]} {meta}"
        text = self.help or ""
        if self.show_default and (self.default is not None):
            text = (text + " " if text else "") + f"[default: {self.default}]"
        return (parts[0] if parts else self.name, text)


class Argument(Parameter):
    param_type_name = "argument"

    def __init__(
        self,
        name,
        required=True,
        default=None,
        type=str,
        metavar=None,
        nargs=1,
        envvar=None,
        expose_value=True,
        show_default=False,
    ):
        super().__init__(
            name=name,
            required=required,
            default=default,
            help=None,
            type=type,
            metavar=metavar,
            nargs=nargs,
            envvar=envvar,
            expose_value=expose_value,
            prompt=False,
            is_eager=False,
            show_default=show_default,
        )

    def get_help_record(self, ctx):
        return None


# Command and Group


class Command:
    def __init__(self, name=None, params=None, callback=None, help=None, short_help=None, context_settings=None):
        self.name = name
        self.params = list(params or [])
        self.callback = callback
        self.help = help
        self.short_help = short_help
        self.context_settings = context_settings or {}
        self.add_default_help_option = True

    def get_usage(self, ctx):
        usage = f"Usage: {ctx.command_path or self.name or 'command'}"
        if self.params:
            usage += " [OPTIONS]"
        # Arguments portion
        arg_parts = []
        for p in self.params:
            if isinstance(p, Argument):
                disp = p.metavar or p.name.upper()
                if p.nargs == -1:
                    disp = disp + "..."
                if not p.required and p.default is not None:
                    disp = f"[{disp}]"
                arg_parts.append(disp)
        if arg_parts:
            usage += " " + " ".join(arg_parts)
        # Group commands handled in Group.get_usage
        return usage

    def format_options(self, ctx):
        # Build options help text
        lines = []
        # Always include help option
        help_opt = Option(("-h", "--help"), help="Show this message and exit.", is_flag=True)
        opts = [help_opt] + [p for p in self.params if isinstance(p, Option)]
        for opt in opts:
            rec = opt.get_help_record(ctx)
            if rec:
                lines.append(f"  {rec[0]:20} {rec[1]}".rstrip())
        return "\n".join(lines)

    def get_help(self, ctx):
        parts = []
        parts.append(self.get_usage(ctx))
        parts.append("")
        # Description/help
        help_text = self.help or (self.callback.__doc__.strip() if getattr(self.callback, "__doc__", None) else "")
        if help_text:
            parts.append(help_text)
            parts.append("")
        # Options
        options = self.format_options(ctx)
        if options:
            parts.append("Options:")
            parts.append(options)
        return "\n".join(parts).rstrip() + "\n"

    def make_context(self, info_name, args, parent=None, obj=None):
        ctx = Context(self, parent=parent, info_name=info_name, obj=obj)
        return ctx

    def parse_args(self, ctx, args):
        # parse options and arguments for this command
        values = {}
        # map option strings to Option
        opt_map = {}
        for p in self.params:
            if isinstance(p, Option):
                for o in p.opts:
                    opt_map[o] = p
        # Include help option
        help_opt = Option(("-h", "--help"), is_flag=True, help="Show this message and exit.")
        for o in help_opt.opts:
            opt_map[o] = help_opt

        positionals = []
        i = 0
        while i < len(args):
            token = args[i]
            if token == "--":
                # everything after is positional
                positionals.extend(args[i + 1 :])
                break
            if token.startswith("--"):
                if "=" in token:
                    opt, val = token.split("=", 1)
                else:
                    opt, val = token, None
                if opt not in opt_map:
                    raise UsageError(f"No such option: {opt}", ctx=ctx)
                opt_obj = opt_map[opt]
                if opt_obj is help_opt:
                    # show help
                    termui = __import__("click.termui", fromlist=["echo"])
                    echo = getattr(termui, "echo")
                    echo(self.get_help(ctx))
                    raise SystemExit(0)
                if isinstance(opt_obj, Option) and opt_obj.is_flag:
                    values[opt_obj.name] = opt_obj.flag_value
                    i += 1
                    continue
                # takes value
                if val is None:
                    if i + 1 >= len(args):
                        raise UsageError(f"Option {opt} requires an argument.", ctx=ctx)
                    val = args[i + 1]
                    i += 2
                else:
                    i += 1
                values[opt_obj.name] = opt_obj.convert(val, ctx)
                continue
            if token.startswith("-") and token != "-":
                # handle short options possibly bundled
                s = token[1:]
                j = 0
                consumed = False
                while j < len(s):
                    so = "-" + s[j]
                    if so not in opt_map:
                        raise UsageError(f"No such option: {so}", ctx=ctx)
                    opt_obj = opt_map[so]
                    if opt_obj is help_opt:
                        termui = __import__("click.termui", fromlist=["echo"])
                        echo = getattr(termui, "echo")
                        echo(self.get_help(ctx))
                        raise SystemExit(0)
                    if isinstance(opt_obj, Option) and opt_obj.is_flag:
                        values[opt_obj.name] = opt_obj.flag_value
                        j += 1
                        continue
                    # takes value: the rest of s or next arg
                    if j + 1 < len(s):
                        val = s[j + 1 :]
                        j = len(s)
                        consumed = True
                    else:
                        if i + 1 >= len(args):
                            raise UsageError(f"Option {so} requires an argument.", ctx=ctx)
                        val = args[i + 1]
                        i += 1
                        j = len(s)
                    values[opt_obj.name] = opt_obj.convert(val, ctx)
                i += 1
                continue
            # positional
            positionals.append(token)
            i += 1

        # Now handle arguments by order of Argument params
        arg_params = [p for p in self.params if isinstance(p, Argument)]
        pos = positionals[:]
        for ap in arg_params:
            if ap.nargs == -1:
                val, pos = ap.process_value(pos, ctx)
            else:
                # if no positional provided, use default if available else error
                if len(pos) == 0 and ap.default is not None and not ap.required:
                    values[ap.name] = ap.default
                    continue
                if len(pos) == 0 and ap.required and ap.default is None:
                    ap.fail_missing(ctx)
                val, pos = ap.process_value(pos, ctx)
            values[ap.name] = val
        if pos:
            # too many arguments
            raise UsageError(f"Got unexpected extra argument{'s' if len(pos)>1 else ''} ({' '.join(pos)}).", ctx=ctx)

        # Fill defaults for options not provided
        for p in self.params:
            if isinstance(p, Option) and p.name not in values:
                if p.prompt and (p.required or p.default is None):
                    # prompt user
                    prom = p.prompt if isinstance(p.prompt, str) else f"{p.name}: "
                    # write prompt
                    termui = __import__("click.termui", fromlist=["echo"])
                    echo = getattr(termui, "echo")
                    echo(prom, nl=False)
                    try:
                        inp = sys.stdin.readline()
                    except Exception:
                        inp = ""
                    inp = inp.rstrip("\n")
                    if inp == "" and p.default is not None:
                        values[p.name] = p.default
                    else:
                        values[p.name] = p.convert(inp, ctx)
                else:
                    values[p.name] = p.get_default(ctx)
        return values

    def invoke(self, ctx):
        # Build kwargs for callback from ctx.params
        kwargs = {}
        for p in self.params:
            if not p.expose_value:
                continue
            if isinstance(p, (Option, Argument)):
                kwargs[p.name] = ctx.params.get(p.name, p.get_default(ctx))
        cb = self.callback
        if cb is None:
            return None
        # pass context?
        if getattr(cb, "__click_pass_context__", False):
            return cb(ctx, **kwargs)
        else:
            return cb(**kwargs)

    def main(self, args=None, prog_name=None, standalone_mode=True, obj=None):
        if args is None:
            args = sys.argv[1:]
        if isinstance(args, str):
            args = shlex.split(args)
        ctx = self.make_context(prog_name or (self.name or ""), args)
        try:
            values = self.parse_args(ctx, args)
            ctx.params.update(values)
            rv = self.invoke(ctx)
            return rv
        except ClickException as e:
            if standalone_mode:
                e.show()
                raise SystemExit(e.exit_code)
            else:
                raise
        except SystemExit:
            # re-raise system exits unless standalone converts
            if standalone_mode:
                raise
            else:
                raise
        except Exception as e:
            if standalone_mode:
                # show generic error
                ce = ClickException(str(e))
                ce.show()
                raise SystemExit(1)
            else:
                raise


class Group(Command):
    def __init__(self, name=None, params=None, callback=None, help=None, short_help=None, context_settings=None):
        super().__init__(name=name, params=params, callback=callback, help=help, short_help=short_help, context_settings=context_settings)
        self.commands = {}

    def add_command(self, cmd, name=None):
        name = name or cmd.name
        if not name:
            raise TypeError("Command needs a name.")
        self.commands[name] = cmd

    def command(self, name=None, **attrs):
        def decorator(f):
            cmd_name = name or f.__name__.replace("_", "-")
            from .decorators import command as _command

            cmd = _command(name=cmd_name, **attrs)(f)
            self.add_command(cmd, cmd_name)
            return cmd

        return decorator

    def group(self, name=None, **attrs):
        def decorator(f):
            grp_name = name or f.__name__.replace("_", "-")
            from .decorators import group as _group

            grp = _group(name=grp_name, **attrs)(f)
            self.add_command(grp, grp_name)
            return grp

        return decorator

    def format_commands(self, ctx):
        # Return help entries for commands
        lines = []
        if not self.commands:
            return ""
        # Compute width
        names = sorted(self.commands.keys())
        for name in names:
            cmd = self.commands[name]
            short = cmd.short_help or (cmd.help.splitlines()[0] if cmd.help else "")
            lines.append(f"  {name:20} {short}".rstrip())
        return "\n".join(lines)

    def get_usage(self, ctx):
        usage = f"Usage: {ctx.command_path or self.name or 'command'}"
        if self.params:
            usage += " [OPTIONS]"
        usage += " COMMAND [ARGS]..."
        return usage

    def get_help(self, ctx):
        parts = []
        parts.append(self.get_usage(ctx))
        parts.append("")
        help_text = self.help or (self.callback.__doc__.strip() if getattr(self.callback, "__doc__", None) else "")
        if help_text:
            parts.append(help_text)
            parts.append("")
        options = self.format_options(ctx)
        if options:
            parts.append("Options:")
            parts.append(options)
            parts.append("")
        cmds = self.format_commands(ctx)
        if cmds:
            parts.append("Commands:")
            parts.append(cmds)
        return "\n".join(parts).rstrip() + "\n"

    def main(self, args=None, prog_name=None, standalone_mode=True, obj=None):
        if args is None:
            args = sys.argv[1:]
        if isinstance(args, str):
            args = shlex.split(args)
        ctx = self.make_context(prog_name or (self.name or ""), args)
        try:
            # parse group-level options and detect subcommand
            values, rest, help_triggered = self.parse_group_args(ctx, args)
            ctx.params.update(values)
            if help_triggered:
                termui = __import__("click.termui", fromlist=["echo"])
                echo = getattr(termui, "echo")
                echo(self.get_help(ctx))
                raise SystemExit(0)
            # If there is a subcommand to invoke:
            sub_cmd = None
            sub_name = None
            if rest:
                token = rest[0]
                if token in self.commands:
                    sub_cmd = self.commands[token]
                    sub_name = token
                    rest = rest[1:]
                else:
                    raise UsageError(f"No such command '{token}'.", ctx=ctx)
            if sub_cmd is None:
                # invoke group callback if any
                rv = self.invoke(ctx)
                return rv
            # create subcontext with path including sub command
            sub_ctx = Context(sub_cmd, parent=ctx, info_name=sub_name, obj=obj)
            # Use sub_cmd.main style but avoid recursion to handle standalone flag
            try:
                values = sub_cmd.parse_args(sub_ctx, rest)
                sub_ctx.params.update(values)
                rv = sub_cmd.invoke(sub_ctx)
                return rv
            except ClickException as e:
                if standalone_mode:
                    e.show()
                    raise SystemExit(e.exit_code)
                else:
                    raise
            except SystemExit:
                if standalone_mode:
                    raise
                else:
                    raise
            except Exception as e:
                if standalone_mode:
                    ce = ClickException(str(e))
                    ce.show()
                    raise SystemExit(1)
                else:
                    raise
        except ClickException as e:
            if standalone_mode:
                e.show()
                raise SystemExit(e.exit_code)
            else:
                raise
        except SystemExit:
            if standalone_mode:
                raise
            else:
                raise
        except Exception as e:
            if standalone_mode:
                ce = ClickException(str(e))
                ce.show()
                raise SystemExit(1)
            else:
                raise

    def parse_group_args(self, ctx, args):
        # Similar parsing to Command.parse_args but stop at subcommand token.
        values = {}
        opt_map = {}
        for p in self.params:
            if isinstance(p, Option):
                for o in p.opts:
                    opt_map[o] = p
        help_opt = Option(("-h", "--help"), is_flag=True, help="Show this message and exit.")
        for o in help_opt.opts:
            opt_map[o] = help_opt

        rest = []
        i = 0
        help_triggered = False
        while i < len(args):
            token = args[i]
            if token == "--":
                rest.extend(args[i + 1 :])
                break
            if token.startswith("-") and token != "-":
                # options
                if token.startswith("--"):
                    if "=" in token:
                        opt, val = token.split("=", 1)
                    else:
                        opt, val = token, None
                    if opt not in opt_map:
                        # Not a known option for group; maybe it's subcommand or subcommand option after name?
                        rest = args[i:]
                        break
                    opt_obj = opt_map[opt]
                    if opt_obj is help_opt:
                        help_triggered = True
                        i += 1
                        continue
                    if opt_obj.is_flag:
                        values[opt_obj.name] = opt_obj.flag_value
                        i += 1
                    else:
                        if val is None:
                            if i + 1 >= len(args):
                                raise UsageError(f"Option {opt} requires an argument.", ctx=ctx)
                            val = args[i + 1]
                            i += 2
                        else:
                            i += 1
                        values[opt_obj.name] = opt_obj.convert(val, ctx)
                    continue
                else:
                    # short(s)
                    s = token[1:]
                    j = 0
                    unknown_short = False
                    while j < len(s):
                        so = "-" + s[j]
                        if so not in opt_map:
                            unknown_short = True
                            break
                        opt_obj = opt_map[so]
                        if opt_obj is help_opt:
                            help_triggered = True
                            j += 1
                            continue
                        if opt_obj.is_flag:
                            values[opt_obj.name] = opt_obj.flag_value
                            j += 1
                        else:
                            if j + 1 < len(s):
                                val = s[j + 1 :]
                                j = len(s)
                                i += 1
                            else:
                                if i + 1 >= len(args):
                                    raise UsageError(f"Option {so} requires an argument.", ctx=ctx)
                                val = args[i + 1]
                                i += 2
                                j = len(s)
                            values[opt_obj.name] = opt_obj.convert(val, ctx)
                            break
                    if unknown_short:
                        rest = args[i:]
                        break
                    else:
                        continue
            else:
                # first positional: subcommand name maybe
                rest = args[i:]
                break
            i += 1
        return values, rest, help_triggered