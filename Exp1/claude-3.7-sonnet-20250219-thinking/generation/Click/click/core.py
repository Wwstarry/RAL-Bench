# -*- coding: utf-8 -*-
"""
    click.core
    ~~~~~~~~~~

    This module implements the central click functionality.
"""

import os
import sys
import inspect
import functools
from collections import OrderedDict

from .utils import echo


class ClickException(Exception):
    """An exception that Click can handle and show to the user."""
    exit_code = 1

    def __init__(self, message):
        self.message = message
        super().__init__(message)
    
    def show(self, file=None):
        if file is None:
            file = sys.stderr
        echo(f"Error: {self.message}", file=file)


class UsageError(ClickException):
    """An internal exception that signals a usage error."""
    exit_code = 2


class Parameter:
    """Represents a parameter to a command."""
    
    def __init__(self, param_decls=None, type=None, required=False,
                 default=None, callback=None, nargs=1, metavar=None,
                 expose_value=True, is_flag=None, flag_value=None,
                 multiple=False, count=False, prompt=False, hide_input=False,
                 is_eager=False, help=None):
        self.param_decls = param_decls or ()
        self.type = type
        self.required = required
        self.default = default
        self.callback = callback
        self.nargs = nargs
        self.metavar = metavar
        self.expose_value = expose_value
        self.is_flag = is_flag
        self.flag_value = flag_value
        self.multiple = multiple
        self.count = count
        self.prompt = prompt
        self.hide_input = hide_input
        self.is_eager = is_eager
        self.help = help
        
        # Process declarations
        self.name = None
        self.opts = []
        self.secondary_opts = []
        for decl in self.param_decls:
            if decl.startswith('--'):
                self.opts.append(decl)
            elif decl.startswith('-'):
                self.secondary_opts.append(decl)
            else:
                self.name = decl
                
        if not self.name:
            if self.opts:
                self.name = self.opts[0].lstrip('-').replace('-', '_')
            elif self.secondary_opts:
                self.name = self.secondary_opts[0].lstrip('-')
            else:
                self.name = 'param'
        
    def get_default(self, ctx):
        """Returns the default value."""
        return self.default
        
    def handle_parse_result(self, ctx, opts, args):
        """Handle parsing results."""
        value = self.get_default(ctx)
        
        if self.name in opts:
            value = opts[self.name]
            
        if self.callback is not None:
            value = self.callback(ctx, self, value)
            
        if self.expose_value:
            ctx.params[self.name] = value
            
        return value


class Option(Parameter):
    """Represents a command line option."""
    
    def __init__(self, param_decls=None, show_default=False, prompt=False,
                 confirmation_prompt=False, hide_input=False, is_flag=None,
                 flag_value=None, multiple=False, count=False, required=False,
                 help=None, type=None, **attrs):
        if is_flag is None:
            if flag_value is not None:
                is_flag = True
            else:
                is_flag = False
                
        if is_flag and flag_value is None:
            flag_value = True
            
        Parameter.__init__(
            self, param_decls, type=type, required=required, help=help,
            is_flag=is_flag, flag_value=flag_value, multiple=multiple,
            count=count, prompt=prompt, hide_input=hide_input, **attrs
        )
        self.show_default = show_default
        self.confirmation_prompt = confirmation_prompt


class Argument(Parameter):
    """Represents a command line argument."""
    
    def __init__(self, param_decls=None, type=None, required=True,
                 default=None, nargs=1, **attrs):
        Parameter.__init__(
            self, param_decls, type=type, required=required,
            default=default, nargs=nargs, **attrs
        )
        

class Context:
    """The context object holds state for the command invocation."""
    
    def __init__(self, command, parent=None, info_name=None, obj=None, **extra):
        self.command = command
        self.parent = parent
        self.info_name = info_name
        self.obj = obj
        self.params = {}
        self.args = []
        self.protected_args = []
        self.resilient_parsing = False
        for key, value in extra.items():
            setattr(self, key, value)
    
    def invoke(self, callback, *args, **kwargs):
        """Invokes the callback with the arguments."""
        return callback(*args, **kwargs)
    
    def forward(self, cmd, *args, **kwargs):
        """Forward the invocation to a different command."""
        return self.invoke(cmd.callback, *args, **kwargs)
    
    def fail(self, message):
        """Aborts the execution with a specific error message."""
        raise UsageError(message)
    
    def exit(self, code=0):
        """Exits the application with the given exit code."""
        sys.exit(code)
    
    def get_usage(self):
        """Get the usage string for the command."""
        return self.command.get_usage(self)
    
    def get_help(self):
        """Get the help string for the command."""
        return self.command.get_help(self)


class Command:
    """Represents a CLI command."""
    
    def __init__(self, name, callback, params=None, help=None, epilog=None, 
                 short_help=None, options_metavar='[OPTIONS]',
                 add_help_option=True):
        self.name = name
        self.callback = callback
        self.params = params or []
        self.help = help
        self.epilog = epilog
        self.short_help = short_help or help
        self.options_metavar = options_metavar
        self.add_help_option = add_help_option
        
        if callback and not params:
            self.params = self._parse_callback_params(callback)
        
        # Apply function attributes
        if callback:
            functools.update_wrapper(self, callback)
            
    def _parse_callback_params(self, callback):
        """Parse parameters from the callback."""
        params = getattr(callback, '__click_params__', [])
        params.reverse()
        return params
        
    def get_help(self, ctx):
        """Get the help string for this command."""
        help_text = self.get_usage(ctx) + "\n\n"
        
        if self.help:
            help_text += self.help + "\n\n"
            
        if self.params:
            help_text += "Options:\n"
            for param in self.params:
                if isinstance(param, Option):
                    help_line = "  " + ", ".join(param.opts + param.secondary_opts)
                    if param.help:
                        help_line += f"  {param.help}"
                    if param.default is not None and param.show_default:
                        help_line += f" [default: {param.default}]"
                    help_text += help_line + "\n"
                elif isinstance(param, Argument):
                    help_line = f"  {param.name}"
                    if param.help:
                        help_line += f"  {param.help}"
                    help_text += help_line + "\n"
            
        if self.epilog:
            help_text += "\n" + self.epilog
            
        return help_text
    
    def get_usage(self, ctx):
        """Get the usage string for this command."""
        pieces = [f"Usage: {ctx.info_name or self.name}"]
        
        for param in self.params:
            if isinstance(param, Option):
                if param.required:
                    pieces.append(f"[{param.name}]")
            elif isinstance(param, Argument):
                pieces.append(f"{param.name}")
                
        return " ".join(pieces)
    
    def make_context(self, info_name, args, parent=None, **extra):
        """Creates a new context for this command."""
        ctx = Context(self, parent=parent, info_name=info_name, **extra)
        self.parse_args(ctx, args)
        return ctx
    
    def parse_args(self, ctx, args):
        """Parse arguments for this command."""
        opts = {}
        pos_args = []
        
        i = 0
        while i < len(args):
            arg = args[i]
            i += 1
            
            # Parse options
            if arg.startswith('--'):
                param_name = arg[2:]
                found_param = None
                for param in self.params:
                    if isinstance(param, Option) and f"--{param_name}" in param.opts:
                        found_param = param
                        break
                
                if found_param:
                    if found_param.is_flag:
                        opts[found_param.name] = found_param.flag_value
                    else:
                        if i >= len(args):
                            ctx.fail(f"Option '{arg}' requires an argument")
                        opts[found_param.name] = args[i]
                        i += 1
                else:
                    ctx.fail(f"No such option: {arg}")
                    
            # Parse short options
            elif arg.startswith('-') and len(arg) > 1:
                short_opt = arg[1:]
                found_param = None
                for param in self.params:
                    if isinstance(param, Option) and f"-{short_opt}" in param.secondary_opts:
                        found_param = param
                        break
                
                if found_param:
                    if found_param.is_flag:
                        opts[found_param.name] = found_param.flag_value
                    else:
                        if i >= len(args):
                            ctx.fail(f"Option '{arg}' requires an argument")
                        opts[found_param.name] = args[i]
                        i += 1
                else:
                    ctx.fail(f"No such option: {arg}")
                    
            # Parse positional arguments
            else:
                pos_args.append(arg)
        
        # Process arguments
        arg_params = [p for p in self.params if isinstance(p, Argument)]
        for i, param in enumerate(arg_params):
            if i < len(pos_args):
                opts[param.name] = pos_args[i]
            elif param.required:
                ctx.fail(f"Missing argument: {param.name}")
        
        # Check for required options
        for param in self.params:
            if param.required and param.name not in opts:
                ctx.fail(f"Missing required option: {param.name}")
            
            param.handle_parse_result(ctx, opts, pos_args)
        
        ctx.args = pos_args[len(arg_params):]
        ctx.params.update(opts)
        
    def invoke(self, ctx):
        """Invoke the command."""
        return ctx.invoke(self.callback, **ctx.params)
    
    def main(self, args=None, prog_name=None, **extra):
        """Main entry point for the command."""
        if args is None:
            args = sys.argv[1:]
            
        info_name = prog_name or self.name
        
        try:
            ctx = self.make_context(info_name, args, **extra)
            result = self.invoke(ctx)
            return result
        except ClickException as e:
            e.show()
            sys.exit(e.exit_code)
        except Exception:
            # Unexpected error
            echo(f"Error: An unexpected error occurred.", err=True)
            sys.exit(1)


class Group(Command):
    """A command group that can have subcommands."""
    
    def __init__(self, name=None, commands=None, **attrs):
        Command.__init__(self, name, callback=None, **attrs)
        self.commands = OrderedDict()
        if commands:
            for name, cmd in commands.items():
                self.add_command(cmd, name)
                
    def add_command(self, cmd, name=None):
        """Add a command to this group."""
        if name is None:
            name = cmd.name
        if name is None:
            raise TypeError("Command has no name")
        self.commands[name] = cmd
        
    def command(self, *args, **kwargs):
        """Create a new command and attach it to this group."""
        from .decorators import command
        def decorator(f):
            cmd = command(*args, **kwargs)(f)
            self.add_command(cmd)
            return cmd
        return decorator
        
    def group(self, *args, **kwargs):
        """Create a new group and attach it to this group."""
        from .decorators import group
        def decorator(f):
            cmd = group(*args, **kwargs)(f)
            self.add_command(cmd)
            return cmd
        return decorator
        
    def get_command(self, ctx, name):
        """Get a command by name."""
        return self.commands.get(name)
        
    def list_commands(self, ctx):
        """List all commands in this group."""
        return sorted(self.commands.keys())
        
    def parse_args(self, ctx, args):
        """Parse arguments for this group."""
        if not args:
            return Command.parse_args(self, ctx, args)
            
        cmd_name = args[0]
        cmd = self.get_command(ctx, cmd_name)
        
        if cmd is None:
            ctx.fail(f"No such command: {cmd_name}")
            
        ctx.protected_args = [cmd_name] + ctx.protected_args
        return Command.parse_args(self, ctx, args)
        
    def invoke(self, ctx):
        """Invoke this group."""
        if not ctx.protected_args:
            return Command.invoke(self, ctx)
            
        cmd_name = ctx.protected_args.pop(0)
        cmd = self.get_command(ctx, cmd_name)
        
        if cmd is None:
            ctx.fail(f"No such command: {cmd_name}")
            
        sub_ctx = cmd.make_context(cmd_name, ctx.args, parent=ctx)
        return cmd.invoke(sub_ctx)
        
    def get_help(self, ctx):
        """Get the help string for this group."""
        help_text = super().get_help(ctx)
        
        if self.commands:
            help_text += "\nCommands:\n"
            for name, cmd in sorted(self.commands.items()):
                help_text += f"  {name}"
                if cmd.short_help:
                    help_text += f"  {cmd.short_help}"
                help_text += "\n"
                
        return help_text