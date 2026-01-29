"""
Core components of the Click framework.
"""

import os
import sys
import inspect
import argparse
from functools import update_wrapper
from gettext import gettext as _

class ClickException(Exception):
    """An exception that Click can handle and show to the user."""
    
    def __init__(self, message):
        super().__init__(message)
        self.message = message
    
    def show(self, file=None):
        if file is None:
            file = sys.stderr
        echo(f"Error: {self.message}", file=file)

class UsageError(ClickException):
    """An internal exception that signals a usage error."""
    pass

class BadParameter(ClickException):
    """An exception that signals a bad parameter."""
    
    def __init__(self, message, ctx=None, param=None, param_hint=None):
        super().__init__(message)
        self.ctx = ctx
        self.param = param
        self.param_hint = param_hint

class Abort(ClickException):
    """An internal exception that signals an abort."""
    pass

class Exit(ClickException):
    """An exception that signals an exit."""
    
    def __init__(self, exit_code=0):
        super().__init__("")
        self.exit_code = exit_code

class Parameter:
    """A parameter base class."""
    
    def __init__(self, param_decls=None, type=None, required=False, 
                 default=None, callback=None, nargs=None, metavar=None,
                 expose_value=True, is_eager=False, envvar=None, 
                 show_default=False, show_envvar=False, help=None, 
                 hidden=False):
        self.name = None
        self.param_decls = param_decls or []
        self.type = type or str
        self.required = required
        self.default = default
        self.callback = callback
        self.nargs = nargs
        self.metavar = metavar
        self.expose_value = expose_value
        self.is_eager = is_eager
        self.envvar = envvar
        self.show_default = show_default
        self.show_envvar = show_envvar
        self.help = help
        self.hidden = hidden
    
    def get_help_record(self, ctx):
        return None
    
    def full_process_value(self, ctx, value):
        if self.callback is not None:
            value = self.callback(ctx, self, value)
        return value

class Option(Parameter):
    """An option is a parameter that is passed as a flag."""
    
    def __init__(self, param_decls=None, **attrs):
        super().__init__(param_decls, **attrs)
        self.is_flag = attrs.get('is_flag', False)
        self.flag_value = attrs.get('flag_value', None)
        self.multiple = attrs.get('multiple', False)
        self.count = attrs.get('count', False)
        self.allow_from_autoenv = attrs.get('allow_from_autoenv', True)
        self.hidden = attrs.get('hidden', False)

class Argument(Parameter):
    """An argument is a positional parameter."""
    
    def __init__(self, param_decls=None, **attrs):
        super().__init__(param_decls, **attrs)

class Context:
    """The context is a special internal object that holds state relevant
    for the script execution at every single level."""
    
    def __init__(self, command, parent=None, info_name=None, obj=None, 
                 auto_envvar_prefix=None, default_map=None, terminal_width=None,
                 max_content_width=None, resilient_parsing=False, 
                 allow_extra_args=None, allow_interspersed_args=None, 
                 ignore_unknown_options=None, help_option_names=None):
        self.command = command
        self.parent = parent
        self.info_name = info_name
        self.obj = obj
        self.auto_envvar_prefix = auto_envvar_prefix
        self.default_map = default_map or {}
        self.terminal_width = terminal_width
        self.max_content_width = max_content_width
        self.resilient_parsing = resilient_parsing
        self.allow_extra_args = allow_extra_args
        self.allow_interspersed_args = allow_interspersed_args
        self.ignore_unknown_options = ignore_unknown_options
        self.help_option_names = help_option_names or ['--help']
        
        self.protected_args = []
        self.args = []
        self.params = {}
        self.meta = {}
        
        # Callback chain
        self._close_callbacks = []
    
    def invoke(self, *args, **kwargs):
        """Invoke another command as if it was called from the command line."""
        return self.command.invoke(self, *args, **kwargs)
    
    def forward(self, *args, **kwargs):
        """Similar to invoke but forwards the current context."""
        return self.command.forward(self, *args, **kwargs)
    
    def exit(self, code=0):
        """Exit the application with a given exit code."""
        raise Exit(code)
    
    def abort(self):
        """Abort the execution."""
        raise Abort()
    
    def fail(self, message):
        """Abort the execution with an error message."""
        raise UsageError(message)
    
    def get_help(self):
        """Get the help string for the command."""
        return self.command.get_help(self)
    
    def call_on_close(self, callback):
        """Register a callback to be called when the context tears down."""
        self._close_callbacks.append(callback)
    
    def close(self):
        """Close the context and call all close callbacks."""
        for callback in self._close_callbacks:
            callback(self)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, tb):
        self.close()

class BaseCommand:
    """Base class for all commands."""
    
    def __init__(self, name=None, context_settings=None, callback=None, 
                 params=None, help=None, epilog=None, short_help=None,
                 options_metavar='[OPTIONS]', add_help_option=True):
        self.name = name
        self.context_settings = context_settings or {}
        self.callback = callback
        self.params = params or []
        self.help = help
        self.epilog = epilog
        self.short_help = short_help
        self.options_metavar = options_metavar
        self.add_help_option = add_help_option
        
        if self.callback is not None:
            self.__doc__ = self.callback.__doc__
    
    def __call__(self, *args, **kwargs):
        """Alias for :meth:`main`."""
        return self.main(*args, **kwargs)
    
    def main(self, args=None, prog_name=None, complete_var=None, 
             standalone_mode=True, **extra):
        """The main entry point for command execution."""
        try:
            with self.make_context(prog_name, args, **extra) as ctx:
                return self.invoke(ctx)
        except Exit as e:
            if standalone_mode:
                sys.exit(e.exit_code)
            else:
                raise
        except ClickException as e:
            if standalone_mode:
                e.show()
                sys.exit(1)
            else:
                raise
        except Exception as e:
            if standalone_mode:
                echo(f"Error: {str(e)}", err=True)
                sys.exit(1)
            else:
                raise
    
    def make_context(self, info_name, args, parent=None, **extra):
        """Create a new context with the given info name and args."""
        ctx = Context(self, parent=parent, info_name=info_name, **extra)
        self.parse_args(ctx, args or [])
        return ctx
    
    def parse_args(self, ctx, args):
        """Parse the arguments and update the context."""
        parser = self.make_parser(ctx)
        opts, args, param_order = parser.parse_args(args)
        
        for param in self.params:
            value = opts.get(param.name)
            if value is None and param.envvar:
                env_value = os.environ.get(param.envvar)
                if env_value is not None:
                    value = env_value
            
            if value is None and param.required:
                raise BadParameter(f"Missing parameter '{param.name}'")
            
            if value is None:
                value = param.default
            
            ctx.params[param.name] = param.full_process_value(ctx, value)
        
        ctx.args = args
    
    def make_parser(self, ctx):
        """Create an argument parser for this command."""
        parser = _ArgumentParser(ctx)
        
        for param in self.params:
            if isinstance(param, Option):
                parser.add_option(param)
            elif isinstance(param, Argument):
                parser.add_argument(param)
        
        return parser
    
    def invoke(self, ctx):
        """Invoke the command with the given context."""
        if self.callback is not None:
            return ctx.invoke(self.callback, **ctx.params)
        return None
    
    def get_help(self, ctx):
        """Get the help string for this command."""
        parts = []
        
        if self.help:
            parts.append(self.help)
        
        if self.params:
            parts.append("\nParameters:")
            for param in self.params:
                if not param.hidden:
                    record = param.get_help_record(ctx)
                    if record:
                        parts.append(f"  {record}")
        
        if self.epilog:
            parts.append(self.epilog)
        
        return "\n".join(parts)

class Command(BaseCommand):
    """A command is the basic unit of execution."""
    
    def __init__(self, name=None, **attrs):
        super().__init__(name, **attrs)

class MultiCommand(BaseCommand):
    """A multi command is a command that has subcommands."""
    
    def __init__(self, name=None, **attrs):
        super().__init__(name, **attrs)
        self.commands = {}
    
    def add_command(self, cmd, name=None):
        """Add a command to the multi command."""
        name = name or cmd.name
        if name is None:
            raise TypeError("Command has no name")
        self.commands[name] = cmd
    
    def get_command(self, ctx, cmd_name):
        """Get a command by name."""
        return self.commands.get(cmd_name)
    
    def list_commands(self, ctx):
        """List all command names."""
        return sorted(self.commands.keys())

class Group(MultiCommand):
    """A group is a multi command that can have subcommands."""
    
    def __init__(self, name=None, **attrs):
        super().__init__(name, **attrs)

class CommandCollection(MultiCommand):
    """A command collection is a multi command that collects commands
    from multiple sources."""
    
    def __init__(self, name=None, sources=None, **attrs):
        super().__init__(name, **attrs)
        self.sources = sources or []
    
    def list_commands(self, ctx):
        """List all command names from all sources."""
        rv = set()
        for source in self.sources:
            rv.update(source.list_commands(ctx))
        return sorted(rv)
    
    def get_command(self, ctx, cmd_name):
        """Get a command by name from the sources."""
        for source in self.sources:
            rv = source.get_command(ctx, cmd_name)
            if rv is not None:
                return rv
        return None

class _ArgumentParser:
    """Internal argument parser."""
    
    def __init__(self, ctx):
        self.ctx = ctx
        self.options = []
        self.arguments = []
    
    def add_option(self, option):
        """Add an option to the parser."""
        self.options.append(option)
    
    def add_argument(self, argument):
        """Add an argument to the parser."""
        self.arguments.append(argument)
    
    def parse_args(self, args):
        """Parse the arguments."""
        opts = {}
        param_order = []
        remaining_args = []
        
        i = 0
        while i < len(args):
            arg = args[i]
            
            if arg.startswith('--'):
                # Long option
                if '=' in arg:
                    name, value = arg[2:].split('=', 1)
                else:
                    name = arg[2:]
                    value = None
                
                option = self._find_option(name)
                if option:
                    if option.is_flag:
                        opts[option.name] = option.flag_value or True
                    elif value is None:
                        i += 1
                        if i >= len(args):
                            raise BadParameter(f"Option '{arg}' requires an argument")
                        value = args[i]
                        opts[option.name] = value
                    else:
                        opts[option.name] = value
                    param_order.append(option)
                else:
                    remaining_args.append(arg)
            elif arg.startswith('-'):
                # Short option
                name = arg[1:]
                option = self._find_option(name)
                if option:
                    if option.is_flag:
                        opts[option.name] = option.flag_value or True
                    else:
                        i += 1
                        if i >= len(args):
                            raise BadParameter(f"Option '{arg}' requires an argument")
                        value = args[i]
                        opts[option.name] = value
                    param_order.append(option)
                else:
                    remaining_args.append(arg)
            else:
                # Argument
                remaining_args.append(arg)
            
            i += 1
        
        # Process arguments
        for j, argument in enumerate(self.arguments):
            if j < len(remaining_args):
                opts[argument.name] = remaining_args[j]
                param_order.append(argument)
            elif argument.required:
                raise BadParameter(f"Missing argument '{argument.name}'")
            else:
                opts[argument.name] = argument.default
        
        return opts, remaining_args[len(self.arguments):], param_order
    
    def _find_option(self, name):
        """Find an option by name."""
        for option in self.options:
            for decl in option.param_decls:
                if decl.lstrip('-') == name:
                    return option
        return None

def echo(message=None, file=None, nl=True, err=False, color=None):
    """Print a message to the console."""
    if file is None:
        file = sys.stderr if err else sys.stdout
    
    if message is None:
        message = ''
    
    message = str(message)
    if nl:
        message += '\n'
    
    file.write(message)
    file.flush()

def secho(message=None, file=None, nl=True, err=False, color=None):
    """Print a styled message to the console."""
    echo(message, file=file, nl=nl, err=err)