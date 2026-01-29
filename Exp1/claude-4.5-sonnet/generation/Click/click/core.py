"""
Core Click classes.
"""

import sys
import inspect
from .exceptions import ClickException, UsageError, BadParameter, Abort
from .utils import make_str, make_default_short_help


class Context:
    """The context object for a Click command."""
    
    def __init__(self, command, parent=None, info_name=None, obj=None, **kwargs):
        self.command = command
        self.parent = parent
        self.info_name = info_name
        self.obj = obj
        self.params = {}
        self._close_callbacks = []
        self.invoked_subcommand = None
        self.protected = kwargs.get('protected', False)
        self.allow_extra_args = kwargs.get('allow_extra_args', False)
        self.allow_interspersed_args = kwargs.get('allow_interspersed_args', True)
        self.ignore_unknown_options = kwargs.get('ignore_unknown_options', False)
        self.help_option_names = kwargs.get('help_option_names', ['--help'])
        self.token_normalize_func = kwargs.get('token_normalize_func')
        self.resilient_parsing = kwargs.get('resilient_parsing', False)
        self.auto_envvar_prefix = kwargs.get('auto_envvar_prefix')
        self.default_map = kwargs.get('default_map')
        self.color = kwargs.get('color')
        self.max_content_width = kwargs.get('max_content_width')
        self._depth = 0
        if parent is not None:
            self._depth = parent._depth + 1
    
    def exit(self, code=0):
        sys.exit(code)
    
    def abort(self):
        raise Abort()
    
    def fail(self, message):
        raise UsageError(message, self)
    
    def get_usage(self):
        return self.command.get_usage(self)
    
    def get_help(self):
        return self.command.get_help(self)
    
    def invoke(self, callback, *args, **kwargs):
        """Invoke a command callback."""
        with self:
            return callback(*args, **kwargs)
    
    def forward(self, callback, *args, **kwargs):
        """Forward to another command."""
        return self.invoke(callback, *args, **kwargs)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for callback in self._close_callbacks:
            callback()
        return False
    
    def call_on_close(self, callback):
        self._close_callbacks.append(callback)


class Parameter:
    """Base class for parameters."""
    
    param_type_name = "parameter"
    
    def __init__(self, param_decls=None, type=None, required=False, default=None,
                 callback=None, metavar=None, expose_value=True, is_eager=False,
                 envvar=None, **kwargs):
        self.param_decls = param_decls or []
        self.type = type or STRING
        self.required = required
        self.default = default
        self.callback = callback
        self.metavar = metavar
        self.expose_value = expose_value
        self.is_eager = is_eager
        self.envvar = envvar
        self.name = None
        self.opts = []
        self.secondary_opts = []
        
        # Process parameter declarations
        for decl in self.param_decls:
            if decl.startswith('--'):
                self.opts.append(decl)
                if self.name is None:
                    self.name = decl[2:].replace('-', '_')
            elif decl.startswith('-'):
                self.secondary_opts.append(decl)
            else:
                self.name = decl
    
    def get_default(self, ctx):
        """Get the default value."""
        if callable(self.default):
            return self.default()
        return self.default
    
    def process_value(self, ctx, value):
        """Process and validate the value."""
        if value is None:
            value = self.get_default(ctx)
        
        if value is None and self.required:
            raise BadParameter(f"Missing parameter: {self.name}", ctx=ctx, param=self)
        
        if value is not None:
            value = self.type.convert(value, self, ctx)
        
        if self.callback is not None:
            value = self.callback(ctx, self, value)
        
        return value
    
    def get_help_record(self, ctx):
        """Get help record for this parameter."""
        return None


class Option(Parameter):
    """An option parameter."""
    
    param_type_name = "option"
    
    def __init__(self, param_decls=None, show_default=False, prompt=False,
                 confirmation_prompt=False, hide_input=False, is_flag=False,
                 flag_value=None, multiple=False, count=False, allow_from_autoenv=True,
                 help=None, hidden=False, show_choices=True, **kwargs):
        super().__init__(param_decls, **kwargs)
        self.show_default = show_default
        self.prompt = prompt
        self.confirmation_prompt = confirmation_prompt
        self.hide_input = hide_input
        self.is_flag = is_flag
        self.flag_value = flag_value
        self.multiple = multiple
        self.count = count
        self.allow_from_autoenv = allow_from_autoenv
        self.help = help
        self.hidden = hidden
        self.show_choices = show_choices
        
        if self.is_flag:
            if self.flag_value is None:
                self.flag_value = True
            if self.default is None:
                self.default = False
    
    def get_help_record(self, ctx):
        """Get help record for this option."""
        if self.hidden:
            return None
        
        opts = list(self.opts)
        opts.extend(self.secondary_opts)
        
        if self.metavar:
            metavar = self.metavar
        elif self.is_flag:
            metavar = None
        else:
            metavar = self.type.name.upper()
        
        if metavar:
            opts = [f"{opt} {metavar}" for opt in opts]
        
        help_text = self.help or ""
        
        return (", ".join(opts), help_text)


class Argument(Parameter):
    """An argument parameter."""
    
    param_type_name = "argument"
    
    def __init__(self, param_decls, required=None, **kwargs):
        if required is None:
            required = kwargs.get('default') is None
        super().__init__(param_decls, required=required, **kwargs)
    
    def get_help_record(self, ctx):
        """Arguments don't show in help by default."""
        return None


class BaseCommand:
    """Base class for commands."""
    
    def __init__(self, name, callback=None, params=None, help=None,
                 epilog=None, short_help=None, options_metavar='[OPTIONS]',
                 add_help_option=True, hidden=False, deprecated=False,
                 **kwargs):
        self.name = name
        self.callback = callback
        self.params = params or []
        self.help = help
        self.epilog = epilog
        self.short_help = short_help
        self.options_metavar = options_metavar
        self.add_help_option = add_help_option
        self.hidden = hidden
        self.deprecated = deprecated
        self.context_settings = kwargs
    
    def make_context(self, info_name, args, parent=None, **extra):
        """Create a context for this command."""
        ctx = Context(self, parent=parent, info_name=info_name, **self.context_settings)
        ctx.params = {}
        
        with ctx:
            self.parse_args(ctx, args)
        
        return ctx
    
    def parse_args(self, ctx, args):
        """Parse arguments."""
        parser = OptionParser(ctx)
        
        # Add help option if needed
        if self.add_help_option and not any(p.name == 'help' for p in self.params):
            help_option = Option(['--help'], is_flag=True, expose_value=False,
                                is_eager=True, help='Show this message and exit.')
            parser.add_option(help_option)
        
        for param in self.params:
            if isinstance(param, Option):
                parser.add_option(param)
            elif isinstance(param, Argument):
                parser.add_argument(param)
        
        opts, args, order = parser.parse_args(args)
        
        # Process parameters in order
        for param in self.params:
            if param.is_eager:
                value = opts.get(param.name)
                value = param.process_value(ctx, value)
                if param.expose_value:
                    ctx.params[param.name] = value
        
        for param in self.params:
            if not param.is_eager:
                if isinstance(param, Option):
                    value = opts.get(param.name)
                elif isinstance(param, Argument):
                    value = args.pop(0) if args else None
                
                value = param.process_value(ctx, value)
                if param.expose_value:
                    ctx.params[param.name] = value
        
        if args and not ctx.allow_extra_args:
            ctx.fail(f"Got unexpected extra argument{'s' if len(args) > 1 else ''} ({' '.join(args)})")
        
        ctx.args = args
    
    def invoke(self, ctx):
        """Invoke the command."""
        if self.callback is not None:
            return ctx.invoke(self.callback, **ctx.params)
    
    def main(self, args=None, prog_name=None, complete_var=None,
             standalone_mode=True, **extra):
        """Main entry point."""
        if args is None:
            args = sys.argv[1:]
        
        try:
            with self.make_context(prog_name or self.name, args, **extra) as ctx:
                rv = self.invoke(ctx)
                if standalone_mode:
                    sys.exit(0)
                return rv
        except ClickException as e:
            if standalone_mode:
                e.show()
                sys.exit(e.exit_code)
            raise
        except Abort:
            if standalone_mode:
                from .termui import echo
                echo("Aborted!", err=True)
                sys.exit(1)
            raise
    
    def __call__(self, *args, **kwargs):
        """Allow command to be called directly."""
        return self.main(*args, **kwargs)
    
    def get_usage(self, ctx):
        """Get usage string."""
        prog_name = ctx.info_name or self.name
        pieces = [f"Usage: {prog_name}"]
        
        if self.options_metavar:
            pieces.append(self.options_metavar)
        
        for param in self.params:
            if isinstance(param, Argument):
                if param.required:
                    pieces.append(param.name.upper())
                else:
                    pieces.append(f"[{param.name.upper()}]")
        
        return " ".join(pieces)
    
    def get_help(self, ctx):
        """Get help text."""
        formatter = HelpFormatter()
        self.format_help(ctx, formatter)
        return formatter.getvalue()
    
    def format_help(self, ctx, formatter):
        """Format help text."""
        self.format_usage(ctx, formatter)
        self.format_help_text(ctx, formatter)
        self.format_options(ctx, formatter)
        self.format_epilog(ctx, formatter)
    
    def format_usage(self, ctx, formatter):
        """Format usage."""
        formatter.write_usage(self.get_usage(ctx))
    
    def format_help_text(self, ctx, formatter):
        """Format help text."""
        if self.help:
            formatter.write_paragraph()
            formatter.write_text(self.help)
    
    def format_options(self, ctx, formatter):
        """Format options."""
        opts = []
        for param in self.params:
            rv = param.get_help_record(ctx)
            if rv is not None:
                opts.append(rv)
        
        if opts:
            with formatter.section("Options"):
                formatter.write_dl(opts)
    
    def format_epilog(self, ctx, formatter):
        """Format epilog."""
        if self.epilog:
            formatter.write_paragraph()
            formatter.write_text(self.epilog)


class Command(BaseCommand):
    """A basic command."""
    pass


class Group(Command):
    """A command that can have subcommands."""
    
    def __init__(self, name=None, commands=None, **kwargs):
        super().__init__(name, **kwargs)
        self.commands = commands or {}
        self.invoke_without_command = kwargs.get('invoke_without_command', False)
        self.chain = kwargs.get('chain', False)
    
    def add_command(self, cmd, name=None):
        """Add a subcommand."""
        name = name or cmd.name
        self.commands[name] = cmd
    
    def command(self, *args, **kwargs):
        """Decorator to add a command."""
        from .decorators import command
        
        def decorator(f):
            cmd = command(*args, **kwargs)(f)
            self.add_command(cmd)
            return cmd
        
        return decorator
    
    def group(self, *args, **kwargs):
        """Decorator to add a group."""
        from .decorators import group
        
        def decorator(f):
            cmd = group(*args, **kwargs)(f)
            self.add_command(cmd)
            return cmd
        
        return decorator
    
    def get_command(self, ctx, cmd_name):
        """Get a subcommand by name."""
        return self.commands.get(cmd_name)
    
    def list_commands(self, ctx):
        """List all subcommands."""
        return sorted(self.commands.keys())
    
    def parse_args(self, ctx, args):
        """Parse arguments for a group."""
        parser = OptionParser(ctx)
        
        # Add help option if needed
        if self.add_help_option and not any(p.name == 'help' for p in self.params):
            help_option = Option(['--help'], is_flag=True, expose_value=False,
                                is_eager=True, help='Show this message and exit.')
            parser.add_option(help_option)
        
        for param in self.params:
            if isinstance(param, Option):
                parser.add_option(param)
        
        opts, args, order = parser.parse_args(args)
        
        # Process parameters
        for param in self.params:
            if param.is_eager:
                value = opts.get(param.name)
                value = param.process_value(ctx, value)
                if param.expose_value:
                    ctx.params[param.name] = value
        
        for param in self.params:
            if not param.is_eager:
                value = opts.get(param.name)
                value = param.process_value(ctx, value)
                if param.expose_value:
                    ctx.params[param.name] = value
        
        ctx.args = args
    
    def invoke(self, ctx):
        """Invoke the group."""
        def _process_result(value):
            if self.callback is not None:
                value = ctx.invoke(self.callback, **ctx.params)
            return value
        
        if not ctx.args:
            if self.invoke_without_command:
                return _process_result(None)
            ctx.fail("Missing command.")
        
        cmd_name = ctx.args[0]
        cmd = self.get_command(ctx, cmd_name)
        
        if cmd is None:
            ctx.fail(f"No such command '{cmd_name}'.")
        
        ctx.invoked_subcommand = cmd_name
        
        with cmd.make_context(cmd_name, ctx.args[1:], parent=ctx) as sub_ctx:
            with ctx:
                _process_result(None)
                return cmd.invoke(sub_ctx)
    
    def format_options(self, ctx, formatter):
        """Format options."""
        super().format_options(ctx, formatter)
        self.format_commands(ctx, formatter)
    
    def format_commands(self, ctx, formatter):
        """Format subcommands."""
        commands = []
        for name in self.list_commands(ctx):
            cmd = self.get_command(ctx, name)
            if cmd is None or cmd.hidden:
                continue
            
            help_text = cmd.short_help or (cmd.help.split('\n')[0] if cmd.help else '')
            commands.append((name, help_text))
        
        if commands:
            with formatter.section("Commands"):
                formatter.write_dl(commands)


class OptionParser:
    """Simple option parser."""
    
    def __init__(self, ctx):
        self.ctx = ctx
        self.options = {}
        self.arguments = []
    
    def add_option(self, option):
        """Add an option."""
        for opt in option.opts + option.secondary_opts:
            self.options[opt] = option
    
    def add_argument(self, argument):
        """Add an argument."""
        self.arguments.append(argument)
    
    def parse_args(self, args):
        """Parse arguments."""
        opts = {}
        remaining = []
        order = []
        i = 0
        
        while i < len(args):
            arg = args[i]
            
            if arg == '--':
                remaining.extend(args[i+1:])
                break
            
            if arg.startswith('--'):
                # Long option
                if '=' in arg:
                    opt, value = arg.split('=', 1)
                else:
                    opt = arg
                    value = None
                
                if opt in self.options:
                    option = self.options[opt]
                    
                    if option.is_flag:
                        opts[option.name] = option.flag_value
                    elif option.count:
                        opts[option.name] = opts.get(option.name, 0) + 1
                    else:
                        if value is None:
                            if i + 1 >= len(args):
                                self.ctx.fail(f"Option {opt} requires an argument.")
                            i += 1
                            value = args[i]
                        
                        if option.multiple:
                            if option.name not in opts:
                                opts[option.name] = []
                            opts[option.name].append(value)
                        else:
                            opts[option.name] = value
                    
                    order.append(option)
                    
                    # Check for help
                    if option.name == 'help':
                        from .termui import echo
                        echo(self.ctx.get_help())
                        self.ctx.exit(0)
                else:
                    if not self.ctx.ignore_unknown_options:
                        self.ctx.fail(f"No such option: {opt}")
                    remaining.append(arg)
            
            elif arg.startswith('-') and len(arg) > 1 and arg[1] != '-':
                # Short option(s)
                for j, char in enumerate(arg[1:]):
                    opt = f"-{char}"
                    
                    if opt in self.options:
                        option = self.options[opt]
                        
                        if option.is_flag:
                            opts[option.name] = option.flag_value
                        elif option.count:
                            opts[option.name] = opts.get(option.name, 0) + 1
                        else:
                            # Value is rest of this arg or next arg
                            if j + 1 < len(arg) - 1:
                                value = arg[j+2:]
                            else:
                                if i + 1 >= len(args):
                                    self.ctx.fail(f"Option {opt} requires an argument.")
                                i += 1
                                value = args[i]
                            
                            if option.multiple:
                                if option.name not in opts:
                                    opts[option.name] = []
                                opts[option.name].append(value)
                            else:
                                opts[option.name] = value
                            
                            break
                        
                        order.append(option)
                        
                        # Check for help
                        if option.name == 'help':
                            from .termui import echo
                            echo(self.ctx.get_help())
                            self.ctx.exit(0)
                    else:
                        if not self.ctx.ignore_unknown_options:
                            self.ctx.fail(f"No such option: {opt}")
                        remaining.append(arg)
                        break
            else:
                remaining.append(arg)
            
            i += 1
        
        return opts, remaining, order


class HelpFormatter:
    """Format help text."""
    
    def __init__(self, indent_increment=2, width=None):
        self.indent_increment = indent_increment
        self.width = width or 80
        self.current_indent = 0
        self.buffer = []
    
    def write(self, text):
        """Write text."""
        self.buffer.append(text)
    
    def write_usage(self, usage):
        """Write usage."""
        self.write(usage)
        self.write('\n')
    
    def write_paragraph(self):
        """Write paragraph separator."""
        self.write('\n')
    
    def write_text(self, text):
        """Write text."""
        self.write(text)
        self.write('\n')
    
    def write_dl(self, rows, col_max=30, col_spacing=2):
        """Write definition list."""
        for name, help_text in rows:
            self.write(f"  {name}")
            if help_text:
                if len(name) <= col_max:
                    self.write(' ' * (col_max - len(name) + col_spacing))
                    self.write(help_text)
                else:
                    self.write('\n')
                    self.write(' ' * (col_max + col_spacing + 2))
                    self.write(help_text)
            self.write('\n')
    
    def section(self, name):
        """Context manager for a section."""
        return HelpSection(self, name)
    
    def getvalue(self):
        """Get the formatted help."""
        return ''.join(self.buffer)


class HelpSection:
    """Context manager for help sections."""
    
    def __init__(self, formatter, name):
        self.formatter = formatter
        self.name = name
    
    def __enter__(self):
        self.formatter.write('\n')
        self.formatter.write(f"{self.name}:\n")
        return self
    
    def __exit__(self, *args):
        pass


# Type system
class ParamType:
    """Base class for parameter types."""
    
    name = "text"
    
    def convert(self, value, param, ctx):
        """Convert a value."""
        return value
    
    def __repr__(self):
        return f"<{self.__class__.__name__}>"


class StringParamType(ParamType):
    """String parameter type."""
    
    name = "text"
    
    def convert(self, value, param, ctx):
        if isinstance(value, bytes):
            try:
                return value.decode('utf-8')
            except UnicodeDecodeError:
                return value.decode('utf-8', 'replace')
        return str(value)


class IntParamType(ParamType):
    """Integer parameter type."""
    
    name = "integer"
    
    def convert(self, value, param, ctx):
        try:
            return int(value)
        except (ValueError, TypeError):
            self.fail(f"{value!r} is not a valid integer", param, ctx)
    
    def fail(self, message, param, ctx):
        raise BadParameter(message, ctx=ctx, param=param)


class FloatParamType(ParamType):
    """Float parameter type."""
    
    name = "float"
    
    def convert(self, value, param, ctx):
        try:
            return float(value)
        except (ValueError, TypeError):
            self.fail(f"{value!r} is not a valid float", param, ctx)
    
    def fail(self, message, param, ctx):
        raise BadParameter(message, ctx=ctx, param=param)


class BoolParamType(ParamType):
    """Boolean parameter type."""
    
    name = "boolean"
    
    def convert(self, value, param, ctx):
        if isinstance(value, bool):
            return value
        value = str(value).lower()
        if value in ('true', '1', 'yes', 'y'):
            return True
        elif value in ('false', '0', 'no', 'n'):
            return False
        self.fail(f"{value!r} is not a valid boolean", param, ctx)
    
    def fail(self, message, param, ctx):
        raise BadParameter(message, ctx=ctx, param=param)


# Singleton instances
STRING = StringParamType()
INT = IntParamType()
FLOAT = FloatParamType()
BOOL = BoolParamType()