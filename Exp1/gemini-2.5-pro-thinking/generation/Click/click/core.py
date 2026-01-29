# click/core.py

import sys
import os
import inspect

# --- Exceptions ---

class ClickException(Exception):
    """Base exception for Click."""
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def format_message(self):
        return self.message

class UsageError(ClickException):
    """An error that is shown to the user."""
    def __init__(self, message, ctx=None):
        super().__init__(message)
        self.ctx = ctx

# --- Context ---

class Context:
    """The context object holds state for a command invocation."""
    def __init__(self, command, parent=None, info_name=None):
        self.command = command
        self.parent = parent
        self.params = {}
        self.args = []
        self.info_name = info_name
        self.obj = None
        if parent:
            self.obj = parent.obj

    def exit(self, code=0):
        """Exits the application with a given exit code."""
        sys.exit(code)

    def fail(self, message):
        """Aborts execution with a usage error."""
        raise UsageError(message, ctx=self)

    @property
    def command_path(self):
        """The full path to the command."""
        parts = []
        node = self
        while node is not None:
            if node.info_name is not None:
                parts.append(node.info_name)
            node = node.parent
        parts.reverse()
        return " ".join(parts)

# --- Parameters ---

class Parameter:
    """Base class for options and arguments."""
    def __init__(self, param_decls, type=None, help=None, default=None, **attrs):
        self.opts, self.name = self._parse_decls(param_decls)
        self.type = type or str
        self.help = help
        self.default = default
        self.attrs = attrs

    def _parse_decls(self, decls):
        opts = [d for d in decls if d.startswith("-")]
        name = [d for d in decls if not d.startswith("-")][0]
        return opts, name.lower()

    def process_value(self, ctx, value):
        if value is None:
            return None
        try:
            return self.type(value)
        except (ValueError, TypeError):
            ctx.fail(f"Invalid value for {self.name}: '{value}' is not a valid {self.type.__name__}.")

    def get_help_record(self, ctx):
        return None

class Option(Parameter):
    """Represents a command-line option."""
    def __init__(self, param_decls, **attrs):
        super().__init__(param_decls, **attrs)
        self.is_flag = attrs.get('is_flag', False)
        if self.is_flag and self.default is None:
            self.default = False

    def get_help_record(self, ctx):
        opts = ", ".join(self.opts)
        help_text = self.help or ""
        if self.default is not None and not self.is_flag:
            help_text += f"  [default: {self.default}]"
        return (opts, help_text)

class Argument(Parameter):
    """Represents a positional argument."""
    def __init__(self, param_decls, **attrs):
        super().__init__(param_decls, **attrs)
        self.required = attrs.get('required', True)
        if not self.required and 'default' not in attrs:
            self.default = None

# --- Commands ---

class BaseCommand:
    """Base class for commands."""
    def __init__(self, name, callback=None, params=None, help=None):
        self.name = name
        self.callback = callback
        self.params = params or []
        self.help = help or (inspect.getdoc(callback) if callback else None)

    def get_help(self, ctx):
        """Formats the help string for the command."""
        lines = [f"Usage: {ctx.command_path} [OPTIONS]"]
        if isinstance(self, Group):
            lines[0] += " COMMAND [ARGS]..."
        
        if self.help:
            lines.append("\n" + inspect.cleandoc(self.help))
        
        options = [p for p in self.params if isinstance(p, Option)]
        if options:
            lines.append("\nOptions:")
            for opt in options:
                opts, help_text = opt.get_help_record(ctx)
                lines.append(f"  {opts:<20} {help_text}")

        if isinstance(self, Group) and self.commands:
            lines.append("\nCommands:")
            for name, cmd in sorted(self.commands.items()):
                cmd_help = cmd.help.split('\n')[0] if cmd.help else ''
                lines.append(f"  {name:<20} {cmd_help}")
        
        return "\n".join(lines)

    def make_context(self, info_name, args, parent=None, **extra):
        """Creates a context for this command."""
        ctx = Context(self, info_name=info_name, parent=parent)
        ctx.params, ctx.args = self._parse_args(ctx, list(args))
        return ctx

    def _parse_args(self, ctx, args):
        """A simplified argument parser."""
        parsed_params = {p.name: p.default for p in self.params}
        opt_map = {opt: p for p in self.params if isinstance(p, Option) for opt in p.opts}
        
        pos_args = [p for p in self.params if isinstance(p, Argument)]
        
        while args:
            arg = args.pop(0)
            if arg == '--':
                break
            
            if arg.startswith('-'):
                if '=' in arg:
                    opt, val = arg.split('=', 1)
                else:
                    opt, val = arg, None

                if opt not in opt_map:
                    ctx.fail(f"No such option: {opt}")
                
                param = opt_map[opt]
                if param.is_flag:
                    parsed_params[param.name] = True
                else:
                    if val is None:
                        if not args or args[0].startswith('-'):
                            ctx.fail(f"Option '{opt}' requires an argument.")
                        val = args.pop(0)
                    parsed_params[param.name] = param.process_value(ctx, val)
            else:
                if not pos_args:
                    ctx.fail(f"Got unexpected extra argument ({arg})")
                param = pos_args.pop(0)
                parsed_params[param.name] = param.process_value(ctx, arg)
        
        for p in pos_args:
            if p.required and parsed_params.get(p.name) is None:
                ctx.fail(f"Missing argument '{p.name.upper()}'.")

        return parsed_params, args

    def invoke(self, ctx):
        """Invokes the command's callback."""
        if self.callback:
            sig = inspect.signature(self.callback)
            cb_params = sig.parameters
            
            kwargs = {}
            if hasattr(self.callback, "__click_pass_context__"):
                kwargs[next(iter(cb_params))] = ctx

            for name, value in ctx.params.items():
                if name in cb_params:
                    kwargs[name] = value
            return self.callback(**kwargs)

    def main(self, args=None, prog_name=None, **extra):
        """The main entry point for command execution."""
        if args is None:
            args = sys.argv[1:]
        if prog_name is None:
            prog_name = os.path.basename(sys.argv[0])

        try:
            if '--help' in args:
                ctx = self.make_context(prog_name, [])
                echo(self.get_help(ctx))
                ctx.exit()

            ctx = self.make_context(prog_name, args, **extra)
            with ctx:
                return self.invoke(ctx)
        except (ClickException, SystemExit) as e:
            if isinstance(e, SystemExit):
                raise
            if isinstance(e, UsageError):
                echo(f"Error: {e.format_message()}", err=True)
                if e.ctx:
                    echo(self.get_help(e.ctx), err=True)
                sys.exit(2)
            else:
                echo(f"Error: {e.format_message()}", err=True)
                sys.exit(1)

class Command(BaseCommand):
    pass

class Group(Command):
    """A command that can have subcommands."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commands = {}

    def add_command(self, cmd, name=None):
        name = name or cmd.name
        self.commands[name] = cmd

    def get_command(self, ctx, cmd_name):
        return self.commands.get(cmd_name)

    def _parse_args(self, ctx, args):
        """Parse args, separating own options from subcommand."""
        # This is a simplified version. A real one is more complex.
        parser = self._create_parser(ctx)
        opts, args, param_order = parser.parse_args(args=list(args))
        for param in self.params:
            value, name = param.handle_parse_result(ctx, opts, args)
            if name is not None:
                ctx.params[name] = value
        return ctx.params, args

    def invoke(self, ctx):
        """Invoke the group callback, then the subcommand."""
        super().invoke(ctx)
        
        if ctx.args:
            cmd_name = ctx.args[0]
            cmd = self.get_command(ctx, cmd_name)
            if cmd:
                sub_ctx = cmd.make_context(cmd_name, ctx.args[1:], parent=ctx)
                return cmd.invoke(sub_ctx)
            else:
                ctx.fail(f"No such command '{cmd_name}'.")

# --- UI Functions ---

_ansi_colors = {
    "black": 30, "red": 31, "green": 32, "yellow": 33,
    "blue": 34, "magenta": 35, "cyan": 36, "white": 37, "reset": 0,
}

def _get_color_code(color, bold=False):
    if color is None:
        return ""
    code = _ansi_colors.get(color.lower())
    if code is None:
        return ""
    return f"\033[{1 if bold else 0};{code}m"

def echo(message=None, file=None, nl=True, err=False):
    """Prints a message to the console."""
    if file is None:
        file = sys.stderr if err else sys.stdout
    
    if message is None:
        message = ""
    
    if nl:
        message = str(message) + "\n"
    
    file.write(str(message))
    file.flush()

def secho(message=None, file=None, nl=True, err=False, fg=None, bg=None, bold=None, **styles):
    """Prints a styled message to the console."""
    if fg:
        reset_code = _get_color_code("reset")
        color_code = _get_color_code(fg, bold=bold)
        message = f"{color_code}{message}{reset_code}"
    
    echo(message, file=file, nl=nl, err=err)