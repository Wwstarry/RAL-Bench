# -*- coding: utf-8 -*-

import sys
import os
import inspect
import re
from collections import deque

# --- Exceptions ---

class ClickException(Exception):
    """Base exception for Click."""
    def __init__(self, message):
        super(ClickException, self).__init__(message)
        self.message = message

    def format_message(self):
        return self.message

    def __str__(self):
        return self.message

class UsageError(ClickException):
    """An error that is shown to the user."""
    def __init__(self, message, ctx=None):
        super(UsageError, self).__init__(message)
        self.ctx = ctx

class MissingParameter(UsageError):
    """Raised when a required parameter is not provided."""
    def __init__(self, param_name, ctx=None):
        super(MissingParameter, self).__init__(f"Missing parameter: {param_name}", ctx=ctx)
        self.param_name = param_name

# --- Terminal Functions ---

_ansi_colors = {
    'black': 30, 'red': 31, 'green': 32, 'yellow': 33,
    'blue': 34, 'magenta': 35, 'cyan': 36, 'white': 37, 'reset': 0,
}
_ansi_reset_all = '\033[0m'

def echo(message=None, file=None, nl=True, err=False):
    """Prints a message to the console."""
    if file is None:
        file = sys.stderr if err else sys.stdout
    if message:
        file.write(str(message))
    if nl:
        file.write('\n')
    file.flush()

def secho(message=None, file=None, nl=True, err=False, fg=None, bg=None, bold=None, **kwargs):
    """Prints a message to the console with styling."""
    bits = []
    if fg:
        try:
            bits.append(f'\033[{_ansi_colors[fg]}m')
        except KeyError:
            raise TypeError(f'Unknown color {fg!r}')
    if bold:
        bits.append('\033[1m')
    
    if message:
        bits.append(str(message))
    
    if fg or bold:
        bits.append(_ansi_reset_all)

    return echo(''.join(bits), file=file, nl=nl, err=err)

# --- Help Formatting ---

class HelpFormatter:
    """Formats help text."""
    def __init__(self, indent_increment=2, width=78):
        self.width = width
        self.indent_increment = indent_increment
        self.buffer = []

    def write(self, text):
        self.buffer.append(text)

    def write_usage(self, prog, args=''):
        self.write(f"Usage: {prog} {args}\n")

    def write_heading(self, heading):
        self.write(f"\n{heading}\n")

    def write_dl(self, rows, col_max=30, col_spacing=2):
        """Writes a definition list."""
        # Calculate max width of the first column
        first_col_width = min(max(len(row[0]) for row in rows), col_max)
        
        for term, definition in rows:
            self.write('  ')
            self.write(term.ljust(first_col_width + col_spacing))
            if definition:
                self.write(definition)
            self.write('\n')

    def getvalue(self):
        return "".join(self.buffer)

# --- Core Classes ---

class Context:
    """Holds state for a command invocation."""
    def __init__(self, command, parent=None, info_name=None, obj=None):
        self.command = command
        self.parent = parent
        self.info_name = info_name
        self.params = {}
        self.args = []
        self.obj = obj
        if self.parent:
            self.obj = self.parent.obj

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, tb):
        pass

    def exit(self, code=0):
        raise SystemExit(code)

    def fail(self, message):
        raise UsageError(message, ctx=self)

    @property
    def command_path(self):
        if self.parent:
            return f"{self.parent.command_path} {self.info_name}"
        return self.info_name

    def get_help(self):
        return self.command.get_help(self)

class Parameter:
    """Base class for options and arguments."""
    def __init__(self, param_decls, type=None, required=False, default=None, help=None, nargs=1):
        self.name, self.opts, self.secondary_opts = self._parse_decls(param_decls)
        self.type = type or str
        self.required = required
        self.default = default
        self.help = help
        self.nargs = nargs

    def _parse_decls(self, decls):
        name = None
        opts = []
        secondary_opts = []
        for decl in decls:
            if decl.startswith('-'):
                opts.append(decl)
                if decl.startswith('--'):
                    if name is None:
                        name = decl.lstrip('-').replace('-', '_')
                else:
                    secondary_opts.append(decl)
            else:
                if name is not None:
                    raise TypeError("Name is already defined")
                name = decl
        if name is None:
            raise TypeError("Could not determine name for parameter")
        return name, opts, secondary_opts

    def get_default(self, ctx):
        return self.default

    def process_value(self, ctx, value):
        if value is None:
            return None
        if self.type is None or isinstance(value, self.type):
            return value
        try:
            return self.type(value)
        except Exception:
            ctx.fail(f"Invalid value for {self.name}: '{value}' is not a valid {self.type.__name__}.")

    def handle_parse_result(self, ctx, opts, args):
        raise NotImplementedError()

class Option(Parameter):
    """Represents an option."""
    def __init__(self, param_decls, **attrs):
        super(Option, self).__init__(param_decls, **attrs)
        self.is_flag = attrs.get('is_flag', False)
        self.count = attrs.get('count', False)
        if self.is_flag and self.default is None:
            self.default = False
        if self.count:
            self.default = 0

    def handle_parse_result(self, ctx, opts, args):
        value = opts.get(self.name)
        if value is None:
            value = self.get_default(ctx)
        
        if self.count:
            value = len(opts.get(self.name, []))
        elif self.is_flag:
            value = bool(value)
        
        return self.process_value(ctx, value), self.name

class Argument(Parameter):
    """Represents a positional argument."""
    def __init__(self, param_decls, **attrs):
        super(Argument, self).__init__(param_decls, **attrs)
        if self.nargs == -1 and self.default is None:
            self.default = tuple()
        self.required = attrs.get('required', self.default is None)

    def handle_parse_result(self, ctx, opts, args):
        if self.nargs == 1:
            value = args.pop(0) if args else None
        else: # nargs == -1
            value = tuple(args)
            args.clear()

        if value is None:
            value = self.get_default(ctx)
        
        if value is None and self.required:
            raise MissingParameter(self.name, ctx=ctx)
        
        if self.nargs == 1:
            value = self.process_value(ctx, value)
        else:
            value = tuple(self.process_value(ctx, v) for v in value)
        
        return value, self.name

class BaseCommand:
    """Base for Command and Group."""
    def __init__(self, name, callback=None, params=None, help=None, **attrs):
        self.name = name
        self.callback = callback
        self.params = params or []
        self.help = help or (callback.__doc__ if callback else None)
        self.pass_context = attrs.get('pass_context', False)

    def get_params(self, ctx):
        return self.params

    def make_context(self, info_name, args, parent=None, **extra):
        ctx = Context(self, info_name=info_name, parent=parent, **extra)
        ctx.params, ctx.args = self.parse_args(ctx, args)
        return ctx

    def parse_args(self, ctx, args):
        if not args and '--help' in sys.argv:
            echo(self.get_help(ctx))
            ctx.exit()

        parser = self._create_parser(ctx)
        opts, unprocessed_args, _ = parser.parse_args(list(args))
        
        params = {}
        for param in self.get_params(ctx):
            value, name = param.handle_parse_result(ctx, opts, unprocessed_args)
            params[name] = value
        
        if unprocessed_args:
            ctx.fail(f"Got unexpected extra argument(s): {' '.join(unprocessed_args)}")

        return params, []

    def invoke(self, ctx):
        self._check_for_help_option(ctx)
        if self.callback is None:
            return

        kwargs = ctx.params
        if self.pass_context:
            return self.callback(ctx, **kwargs)
        else:
            return self.callback(**kwargs)

    def main(self, args=None, prog_name=None, standalone_mode=True, **extra):
        if args is None:
            args = sys.argv[1:]
        if prog_name is None:
            prog_name = sys.argv[0]

        try:
            try:
                with self.make_context(prog_name, args, **extra) as ctx:
                    return self.invoke(ctx)
            except (EOFError, KeyboardInterrupt):
                echo(file=sys.stderr)
                return 1
            except ClickException as e:
                if not standalone_mode:
                    raise
                e.show()
                return 1
            except Abort:
                if not standalone_mode:
                    raise
                echo('Aborted!', file=sys.stderr)
                return 1
        except SystemExit as e:
            if standalone_mode:
                sys.exit(e.code or 0)
            else:
                # Re-raise for CliRunner
                raise

    def get_help(self, ctx):
        formatter = HelpFormatter()
        
        usage_pieces = [p.name.upper() for p in self.get_params(ctx) if isinstance(p, Argument)]
        if isinstance(self, Group):
            usage_pieces.append('COMMAND [ARGS]...')
        
        formatter.write_usage(ctx.command_path, '[OPTIONS] ' + ' '.join(usage_pieces))
        
        if self.help:
            formatter.write('\n' + self.help.strip() + '\n')

        opts = [p for p in self.get_params(ctx) if isinstance(p, Option)]
        if opts:
            formatter.write_heading("Options:")
            rows = [(', '.join(p.opts), p.help or '') for p in opts]
            formatter.write_dl(rows)

        if isinstance(self, Group):
            formatter.write_heading("Commands:")
            rows = [(name, cmd.help.split('\n')[0] if cmd.help else '') for name, cmd in sorted(self.commands.items())]
            formatter.write_dl(rows)

        return formatter.getvalue()

    def _check_for_help_option(self, ctx):
        for param in self.get_params(ctx):
            if isinstance(param, Option) and param.name == 'help' and ctx.params.get('help'):
                echo(self.get_help(ctx))
                ctx.exit()

    def _create_parser(self, ctx):
        return OptionParser(ctx)

class Command(BaseCommand):
    pass

class Group(Command):
    def __init__(self, *args, **kwargs):
        super(Group, self).__init__(*args, **kwargs)
        self.commands = {}

    def add_command(self, cmd):
        self.commands[cmd.name] = cmd

    def get_command(self, ctx, cmd_name):
        return self.commands.get(cmd_name)

    def parse_args(self, ctx, args):
        parser = self._create_parser(ctx)
        opts, unprocessed_args, _ = parser.parse_args(list(args))

        if unprocessed_args:
            cmd_name = unprocessed_args[0]
            cmd = self.get_command(ctx, cmd_name)
            if cmd:
                ctx.args = unprocessed_args[1:]
                # Command found, so we don't process args for the group
                params = {}
                for param in self.get_params(ctx):
                    value, name = param.handle_parse_result(ctx, opts, [])
                    params[name] = value
                return params, []

        # No command or no args, parse as a normal command
        return super(Group, self).parse_args(ctx, args)

    def invoke(self, ctx):
        self._check_for_help_option(ctx)
        
        if ctx.args:
            cmd_name = ctx.args[0]
            cmd = self.get_command(ctx, cmd_name)
            if cmd:
                return cmd.main(args=ctx.args[1:], prog_name=f"{ctx.command_path} {cmd_name}", standalone_mode=False)

        return super(Group, self).invoke(ctx)

# --- Parser ---

class OptionParser:
    def __init__(self, ctx):
        self.ctx = ctx
        self.opt_map = {}
        for param in ctx.command.get_params(ctx):
            if isinstance(param, Option):
                for opt in param.opts:
                    self.opt_map[opt] = param

    def parse_args(self, args):
        self.args = deque(args)
        self.opts = {}
        self.positional_args = []
        self.order = []

        while self.args:
            arg = self.args.popleft()
            if arg == '--':
                self.positional_args.extend(self.args)
                break
            if arg.startswith('--'):
                self._parse_long_opt(arg)
            elif arg.startswith('-'):
                self._parse_short_opt(arg)
            else:
                self.positional_args.append(arg)
        
        return self.opts, self.positional_args, self.order

    def _parse_long_opt(self, arg):
        if '=' in arg:
            opt_name, value = arg.split('=', 1)
        else:
            opt_name, value = arg, None

        param = self.opt_map.get(opt_name)
        if not param:
            self.ctx.fail(f"No such option: {opt_name}")

        if param.is_flag:
            if value is not None:
                self.ctx.fail(f"{opt_name} is a flag and does not take an argument.")
            self.opts[param.name] = True
        elif param.count:
            self.opts.setdefault(param.name, []).append(1)
        else:
            if value is None:
                if not self.args:
                    self.ctx.fail(f"Option '{opt_name}' requires an argument.")
                value = self.args.popleft()
            self.opts[param.name] = value

    def _parse_short_opt(self, arg):
        opt_str = arg[1:]
        while opt_str:
            opt_char = '-' + opt_str[0]
            param = self.opt_map.get(opt_char)
            if not param:
                self.ctx.fail(f"No such option: {opt_char}")

            opt_str = opt_str[1:]
            if param.is_flag or param.count:
                if param.count:
                    self.opts.setdefault(param.name, []).append(1)
                else:
                    self.opts[param.name] = True
            else:
                if opt_str:
                    value = opt_str
                else:
                    if not self.args:
                        self.ctx.fail(f"Option '{opt_char}' requires an argument.")
                    value = self.args.popleft()
                self.opts[param.name] = value
                break