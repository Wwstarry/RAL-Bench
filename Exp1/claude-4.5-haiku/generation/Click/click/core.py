"""
Core Click classes and functionality.
"""

import sys
import inspect
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from collections import OrderedDict


class Context:
    """Context object for command execution."""
    
    def __init__(
        self,
        command: "Command",
        parent: Optional["Context"] = None,
        info_name: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        **extra
    ):
        self.command = command
        self.parent = parent
        self.info_name = info_name
        self.params = params or {}
        self._meta = extra
        self.obj = None
        self.invoked_subcommand = None
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
    
    def get_parameter_source(self, param_name: str) -> Optional[str]:
        """Get the source of a parameter."""
        return self._meta.get(f"_param_source_{param_name}")


class Parameter:
    """Base class for command parameters."""
    
    def __init__(
        self,
        param_decls: List[str],
        type: Optional[Any] = None,
        required: bool = False,
        default: Any = None,
        callback: Optional[Callable] = None,
        nargs: int = 1,
        multiple: bool = False,
        is_flag: bool = False,
        flag_value: Any = None,
        count: bool = False,
        help: Optional[str] = None,
        show_default: bool = True,
        **extra
    ):
        self.param_decls = param_decls
        self.name = self._get_name(param_decls)
        self.type = type
        self.required = required
        self.default = default
        self.callback = callback
        self.nargs = nargs
        self.multiple = multiple
        self.is_flag = is_flag
        self.flag_value = flag_value
        self.count = count
        self.help = help
        self.show_default = show_default
        self.extra = extra
    
    def _get_name(self, param_decls: List[str]) -> str:
        """Extract parameter name from declarations."""
        for decl in param_decls:
            if not decl.startswith("-"):
                return decl
        # For options, use the longest one without dashes
        decl = max(param_decls, key=len)
        return decl.lstrip("-").replace("-", "_")
    
    def consume_value(self, ctx: Context, opts: Dict[str, Any]) -> Tuple[Any, bool]:
        """Consume a value from options."""
        raise NotImplementedError()
    
    def process_value(self, ctx: Context, value: Any) -> Any:
        """Process the value through type conversion and callback."""
        if value is None and self.default is not None:
            if callable(self.default):
                value = self.default()
            else:
                value = self.default
        
        if value is not None and self.type is not None:
            if isinstance(self.type, type):
                if self.type == bool:
                    value = bool(value)
                elif self.type == int:
                    value = int(value)
                elif self.type == float:
                    value = float(value)
                elif self.type == str:
                    value = str(value)
                else:
                    value = self.type(value)
            elif hasattr(self.type, "convert"):
                value = self.type.convert(value, self, ctx)
        
        if self.callback is not None:
            value = self.callback(ctx, self, value)
        
        return value
    
    def get_help_record(self, ctx: Context) -> Optional[Tuple[str, str]]:
        """Get help text for this parameter."""
        return None


class Argument(Parameter):
    """Represents a command argument."""
    
    def __init__(self, param_decls: List[str], **kwargs):
        kwargs.setdefault("required", True)
        super().__init__(param_decls, **kwargs)
    
    def consume_value(self, ctx: Context, opts: Dict[str, Any]) -> Tuple[Any, bool]:
        """Consume argument value from remaining args."""
        value = opts.get(self.name)
        return value, value is not None


class Option(Parameter):
    """Represents a command option."""
    
    def __init__(
        self,
        param_decls: List[str],
        is_flag: bool = False,
        flag_value: Any = None,
        count: bool = False,
        multiple: bool = False,
        **kwargs
    ):
        super().__init__(
            param_decls,
            is_flag=is_flag,
            flag_value=flag_value,
            count=count,
            multiple=multiple,
            **kwargs
        )
    
    def consume_value(self, ctx: Context, opts: Dict[str, Any]) -> Tuple[Any, bool]:
        """Consume option value from parsed options."""
        value = opts.get(self.name)
        return value, value is not None
    
    def get_help_record(self, ctx: Context) -> Optional[Tuple[str, str]]:
        """Get help text for this option."""
        if self.help is None:
            return None
        
        rv = ", ".join(self.param_decls)
        if self.help:
            rv += "  " + self.help
        return rv, ""


class Command:
    """Represents a command."""
    
    def __init__(
        self,
        name: Optional[str] = None,
        callback: Optional[Callable] = None,
        params: Optional[List[Parameter]] = None,
        help: Optional[str] = None,
        epilog: Optional[str] = None,
        short_help: Optional[str] = None,
        options_metavar: str = "[OPTIONS]",
        add_help_option: bool = True,
        **extra
    ):
        self.name = name
        self.callback = callback
        self.params = params or []
        self.help = help
        self.epilog = epilog
        self.short_help = short_help
        self.options_metavar = options_metavar
        self.add_help_option = add_help_option
        self.extra = extra
    
    def main(
        self,
        args: Optional[List[str]] = None,
        prog_name: Optional[str] = None,
        complete_var: Optional[str] = None,
        standalone_mode: bool = True,
        **extra
    ) -> Any:
        """Execute the command."""
        if args is None:
            args = sys.argv[1:]
        
        try:
            with self.make_context(prog_name or self.name or "cli", args, **extra) as ctx:
                return self.invoke(ctx)
        except SystemExit as e:
            if standalone_mode:
                raise
            return e.code
        except Exception as e:
            if standalone_mode:
                raise
            return 1
    
    def make_context(
        self,
        info_name: str,
        args: List[str],
        parent: Optional[Context] = None,
        **extra
    ) -> Context:
        """Create a context for this command."""
        ctx = Context(self, parent=parent, info_name=info_name, **extra)
        self.parse_args(ctx, args)
        return ctx
    
    def parse_args(self, ctx: Context, args: List[str]) -> List[str]:
        """Parse command line arguments."""
        opts = {}
        args_list = []
        i = 0
        
        while i < len(args):
            arg = args[i]
            
            if arg == "--":
                args_list.extend(args[i+1:])
                break
            elif arg.startswith("-"):
                # Parse option
                if arg.startswith("--"):
                    # Long option
                    if "=" in arg:
                        key, value = arg.split("=", 1)
                        opt_name = key[2:].replace("-", "_")
                        opts[opt_name] = value
                    else:
                        opt_name = arg[2:].replace("-", "_")
                        param = self._find_param(opt_name)
                        if param and param.is_flag:
                            opts[opt_name] = True
                        elif param and param.count:
                            opts[opt_name] = opts.get(opt_name, 0) + 1
                        elif i + 1 < len(args) and not args[i+1].startswith("-"):
                            i += 1
                            opts[opt_name] = args[i]
                        else:
                            opts[opt_name] = True
                else:
                    # Short option(s)
                    for j, char in enumerate(arg[1:]):
                        opt_name = char
                        param = self._find_param(opt_name)
                        if param and param.is_flag:
                            opts[opt_name] = True
                        elif param and param.count:
                            opts[opt_name] = opts.get(opt_name, 0) + 1
                        elif j < len(arg) - 2:
                            # More chars in this arg
                            opts[opt_name] = arg[j+2:]
                            break
                        elif i + 1 < len(args) and not args[i+1].startswith("-"):
                            i += 1
                            opts[opt_name] = args[i]
            else:
                args_list.append(arg)
            
            i += 1
        
        # Process parameters
        for param in self.params:
            if isinstance(param, Option):
                value, provided = param.consume_value(ctx, opts)
                if value is None and param.default is not None:
                    if callable(param.default):
                        value = param.default()
                    else:
                        value = param.default
                ctx.params[param.name] = param.process_value(ctx, value)
            elif isinstance(param, Argument):
                if args_list:
                    value = args_list.pop(0)
                else:
                    value = param.default if param.default is not None else None
                ctx.params[param.name] = param.process_value(ctx, value)
        
        return args_list
    
    def _find_param(self, name: str) -> Optional[Parameter]:
        """Find a parameter by name or short form."""
        for param in self.params:
            if param.name == name:
                return param
            for decl in param.param_decls:
                if decl.lstrip("-") == name:
                    return param
        return None
    
    def invoke(self, ctx: Context) -> Any:
        """Invoke the command."""
        if self.callback is None:
            return None
        
        return ctx.invoke(self.callback, **ctx.params)
    
    def get_help(self, ctx: Context) -> str:
        """Get help text for this command."""
        lines = []
        
        if self.help:
            lines.append(self.help)
            lines.append("")
        
        if self.params:
            lines.append("Options:")
            for param in self.params:
                if isinstance(param, Option):
                    record = param.get_help_record(ctx)
                    if record:
                        lines.append(f"  {record[0]}")
            lines.append("")
        
        if self.epilog:
            lines.append(self.epilog)
        
        return "\n".join(lines)


class Group(Command):
    """Represents a group of commands."""
    
    def __init__(
        self,
        name: Optional[str] = None,
        commands: Optional[Dict[str, Command]] = None,
        **kwargs
    ):
        super().__init__(name=name, **kwargs)
        self.commands = commands or OrderedDict()
    
    def add_command(self, cmd: Command, name: Optional[str] = None) -> None:
        """Add a command to this group."""
        name = name or cmd.name
        self.commands[name] = cmd
    
    def command(
        self,
        name: Optional[str] = None,
        **kwargs
    ) -> Callable:
        """Decorator to add a command to this group."""
        def decorator(f: Callable) -> Callable:
            cmd = Command(name=name or f.__name__, callback=f, **kwargs)
            self.add_command(cmd)
            return f
        return decorator
    
    def group(
        self,
        name: Optional[str] = None,
        **kwargs
    ) -> Callable:
        """Decorator to add a group to this group."""
        def decorator(f: Callable) -> Callable:
            grp = Group(name=name or f.__name__, callback=f, **kwargs)
            self.add_command(grp)
            return f
        return decorator
    
    def parse_args(self, ctx: Context, args: List[str]) -> List[str]:
        """Parse arguments for a group."""
        # First parse options for the group itself
        remaining = super().parse_args(ctx, args)
        
        # Then check for subcommand
        if remaining:
            cmd_name = remaining[0]
            if cmd_name in self.commands:
                ctx.invoked_subcommand = cmd_name
                cmd = self.commands[cmd_name]
                with cmd.make_context(cmd_name, remaining[1:], parent=ctx) as sub_ctx:
                    ctx._subcommand_context = sub_ctx
                    return []
        
        return remaining
    
    def invoke(self, ctx: Context) -> Any:
        """Invoke the group."""
        rv = None
        if self.callback is not None:
            rv = ctx.invoke(self.callback, **ctx.params)
        
        if ctx.invoked_subcommand:
            sub_ctx = ctx._subcommand_context
            cmd = self.commands[ctx.invoked_subcommand]
            rv = cmd.invoke(sub_ctx)
        
        return rv
    
    def get_help(self, ctx: Context) -> str:
        """Get help text for this group."""
        lines = []
        
        if self.help:
            lines.append(self.help)
            lines.append("")
        
        if self.params:
            lines.append("Options:")
            for param in self.params:
                if isinstance(param, Option):
                    record = param.get_help_record(ctx)
                    if record:
                        lines.append(f"  {record[0]}")
            lines.append("")
        
        if self.commands:
            lines.append("Commands:")
            for name, cmd in self.commands.items():
                help_text = cmd.short_help or cmd.help or ""
                lines.append(f"  {name:<20} {help_text}")
            lines.append("")
        
        if self.epilog:
            lines.append(self.epilog)
        
        return "\n".join(lines)


# Extend Context to support invoke
def _context_invoke(self, __callback, *args, **kwargs):
    """Invoke a callback with the given arguments."""
    return __callback(*args, **kwargs)

Context.invoke = _context_invoke