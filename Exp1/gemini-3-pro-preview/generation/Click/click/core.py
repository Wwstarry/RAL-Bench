import sys
from collections import deque
from .exceptions import Exit, Abort, UsageError, BadParameter, MissingParameter
from .utils import echo, get_text_stderr

class Context:
    _stack = []

    def __init__(self, command, parent=None, info_name=None, obj=None, auto_envvar_prefix=None, **kwargs):
        self.command = command
        self.parent = parent
        self.info_name = info_name
        self.params = {}
        self.args = []
        self.obj = obj or (parent.obj if parent else None)
        self.protected_args = []
        self._meta = getattr(parent, 'meta', {})
        self.auto_envvar_prefix = auto_envvar_prefix

    def __enter__(self):
        self._stack.append(self)
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self._stack.pop()

    def get_usage(self):
        return f"Usage: {self.info_name} [OPTIONS] {self.command.name}"

    def invoke(self, callback, **kwargs):
        # Combine params from context and kwargs
        args = self.params.copy()
        args.update(kwargs)
        return callback(**args)

    def forward(self, command, *args, **kwargs):
        # Simplified forward
        return command.callback(*args, **kwargs)

    def fail(self, message):
        raise UsageError(message, self)

    def abort(self):
        raise Abort()

    def exit(self, code=0):
        raise Exit(code)


class Parameter:
    def __init__(self, param_decls, type=None, required=False, default=None, nargs=1, metavar=None, help=None, callback=None, is_eager=False, envvar=None):
        self.name = None
        self.opts = []
        self.secondary_opts = []
        
        for decl in param_decls:
            if decl.startswith('-'):
                self.opts.append(decl)
            else:
                self.name = decl
        
        if self.name is None and self.opts:
            # Derive name from longest option
            self.name = max(self.opts, key=len).lstrip('-').replace('-', '_')

        self.type = type
        self.required = required
        self.default = default
        self.nargs = nargs
        self.metavar = metavar
        self.help = help
        self.callback = callback
        self.is_eager = is_eager
        self.envvar = envvar

    def process_value(self, ctx, value):
        if value is None:
            value = self.default
        
        if self.required and value is None:
            raise MissingParameter(f"Missing parameter: {self.name}", ctx=ctx, param=self)
            
        if self.type is not None and value is not None:
            try:
                if hasattr(self.type, 'convert'):
                    value = self.type.convert(value, self, ctx)
                else:
                    value = self.type(value)
            except Exception as e:
                raise BadParameter(str(e), ctx=ctx, param=self)
        
        if self.callback:
            value = self.callback(ctx, self, value)
            
        return value


class Option(Parameter):
    def __init__(self, param_decls, show_default=None, prompt=False, confirmation_prompt=False, hide_input=False, is_flag=False, flag_value=None, multiple=False, count=False, **kwargs):
        super().__init__(param_decls, **kwargs)
        self.show_default = show_default
        self.prompt = prompt
        self.confirmation_prompt = confirmation_prompt
        self.hide_input = hide_input
        self.is_flag = is_flag
        self.flag_value = flag_value
        self.multiple = multiple
        self.count = count
        
        if is_flag and self.default is None:
            self.default = False


class Argument(Parameter):
    def __init__(self, param_decls, required=None, **kwargs):
        if required is None:
            required = True
        super().__init__(param_decls, required=required, **kwargs)


class BaseCommand:
    def __init__(self, name, context_settings=None):
        self.name = name
        self.context_settings = context_settings or {}

    def make_context(self, info_name, args, parent=None, **extra):
        ctx = Context(self, info_name=info_name, parent=parent, **self.context_settings)
        with ctx:
            self.parse_args(ctx, args)
        return ctx

    def parse_args(self, ctx, args):
        raise NotImplementedError()

    def invoke(self, ctx):
        raise NotImplementedError()

    def main(self, args=None, prog_name=None, complete_var=None, standalone_mode=True, **extra):
        if args is None:
            args = sys.argv[1:]
        else:
            args = list(args)
            
        if prog_name is None:
            prog_name = 'python'

        try:
            try:
                with self.make_context(prog_name, args, **extra) as ctx:
                    rv = self.invoke(ctx)
                    ctx.exit()
            except (EOFError, KeyboardInterrupt):
                raise Abort()
            except Exit as e:
                if standalone_mode:
                    sys.exit(e.exit_code)
                else:
                    return e.exit_code
            except Abort:
                if standalone_mode:
                    echo('Aborted!', file=get_text_stderr())
                    sys.exit(1)
                else:
                    raise
            except ClickException as e:
                if standalone_mode:
                    e.show()
                    sys.exit(1)
                else:
                    raise
        except Exception:
            if not standalone_mode:
                raise
            import traceback
            traceback.print_exc()
            sys.exit(1)


class Command(BaseCommand):
    def __init__(self, name, callback, params=None, help=None, epilog=None, short_help=None, options_metavar='[OPTIONS]', add_help_option=True, hidden=False, deprecated=False):
        super().__init__(name)
        self.callback = callback
        self.params = params or []
        self.help = help
        self.add_help_option = add_help_option

    def invoke(self, ctx):
        if self.callback:
            return ctx.invoke(self.callback, **ctx.params)

    def parse_args(self, ctx, args):
        # Very basic parser implementation
        args = list(args)
        opts = {p.name: None for p in self.params if isinstance(p, Option)}
        
        # Handle flags and options
        remaining_args = []
        i = 0
        while i < len(args):
            arg = args[i]
            matched = False
            
            if arg == '--help' and self.add_help_option:
                echo(ctx.get_usage())
                ctx.exit(0)

            if arg.startswith('-'):
                # Find matching option
                for param in self.params:
                    if isinstance(param, Option) and arg in param.opts:
                        matched = True
                        if param.is_flag:
                            if param.count:
                                current = opts.get(param.name) or 0
                                opts[param.name] = current + 1
                            else:
                                opts[param.name] = param.flag_value if param.flag_value is not None else True
                        else:
                            if i + 1 < len(args):
                                opts[param.name] = args[i+1]
                                i += 1
                            else:
                                raise BadParameter(f"Option {arg} requires an argument", ctx=ctx, param=param)
                        break
            
            if not matched:
                remaining_args.append(arg)
            i += 1

        # Process Options
        for param in self.params:
            if isinstance(param, Option):
                val = opts.get(param.name)
                ctx.params[param.name] = param.process_value(ctx, val)

        # Process Arguments
        arg_params = [p for p in self.params if isinstance(p, Argument)]
        
        if len(remaining_args) < len(arg_params):
             # Check for required args
             for j in range(len(remaining_args), len(arg_params)):
                 if arg_params[j].required:
                     raise MissingParameter(f"Missing argument {arg_params[j].name}", ctx=ctx, param=arg_params[j])

        for j, param in enumerate(arg_params):
            if j < len(remaining_args):
                ctx.params[param.name] = param.process_value(ctx, remaining_args[j])
            else:
                ctx.params[param.name] = param.process_value(ctx, None)
        
        ctx.args = remaining_args[len(arg_params):]


class Group(Command):
    def __init__(self, name=None, commands=None, **attrs):
        super().__init__(name, **attrs)
        self.commands = commands or {}

    def add_command(self, cmd, name=None):
        name = name or cmd.name
        self.commands[name] = cmd

    def get_command(self, ctx, cmd_name):
        return self.commands.get(cmd_name)

    def list_commands(self, ctx):
        return sorted(self.commands.keys())

    def invoke(self, ctx):
        super().invoke(ctx)
        cmd_name = ctx.protected_args[0] if ctx.protected_args else None
        if not cmd_name:
            return
        
        cmd = self.get_command(ctx, cmd_name)
        if cmd is None:
            raise UsageError(f"No such command '{cmd_name}'.", ctx)
            
        with cmd.make_context(cmd_name, ctx.args, parent=ctx) as cmd_ctx:
            return cmd.invoke(cmd_ctx)

    def parse_args(self, ctx, args):
        # Group parsing: parse options, stop at first non-option (subcommand)
        args = list(args)
        opts = {p.name: None for p in self.params if isinstance(p, Option)}
        
        i = 0
        while i < len(args):
            arg = args[i]
            if arg == '--help' and self.add_help_option:
                echo(ctx.get_usage())
                ctx.exit(0)

            if arg.startswith('-'):
                matched = False
                for param in self.params:
                    if isinstance(param, Option) and arg in param.opts:
                        matched = True
                        if param.is_flag:
                            opts[param.name] = True
                        else:
                            if i + 1 < len(args):
                                opts[param.name] = args[i+1]
                                i += 1
                        break
                if not matched:
                    # Unknown option, might belong to subcommand? 
                    # For strict click behavior, groups consume their options, stop at unknown?
                    # Simplified: assume it's a subcommand or arg for subcommand
                    break
            else:
                # Found subcommand
                break
            i += 1
            
        # Process Group Options
        for param in self.params:
            if isinstance(param, Option):
                val = opts.get(param.name)
                ctx.params[param.name] = param.process_value(ctx, val)
        
        ctx.protected_args = args[i:i+1]
        ctx.args = args[i+1:]