"""Main Typer application class."""

import sys
import inspect
from typing import Callable, Optional, Any, Dict, List
from .params import ParamInfo, Option, Argument
from .core import Exit


class Typer:
    """Main Typer application class for building CLI applications."""
    
    def __init__(
        self,
        name: Optional[str] = None,
        help: Optional[str] = None,
        **kwargs: Any
    ):
        self.name = name
        self.help = help
        self.commands: Dict[str, CommandInfo] = {}
        self.callback_func: Optional[Callable] = None
        
    def command(
        self,
        name: Optional[str] = None,
        help: Optional[str] = None,
        **kwargs: Any
    ) -> Callable:
        """Decorator to register a command."""
        def decorator(func: Callable) -> Callable:
            cmd_name = name or func.__name__.replace("_", "-")
            self.commands[cmd_name] = CommandInfo(
                func=func,
                name=cmd_name,
                help=help or func.__doc__,
            )
            return func
        return decorator
    
    def callback(self, **kwargs: Any) -> Callable:
        """Decorator to register a callback function."""
        def decorator(func: Callable) -> Callable:
            self.callback_func = func
            return func
        return decorator
    
    def __call__(self, *args, **kwargs):
        """Make the app callable."""
        return self._run(sys.argv[1:])
    
    def _run(self, args: List[str]) -> int:
        """Run the application with given arguments."""
        # Handle --help
        if "--help" in args or "-h" in args:
            self._print_help()
            return 0
        
        # If no commands registered, this might be a simple callback app
        if not self.commands and self.callback_func:
            try:
                result = self._execute_function(self.callback_func, args)
                return 0 if result is None else result
            except Exit as e:
                return e.code
        
        # Parse command name
        if not args:
            if self.commands:
                self._print_help()
                return 0
            return 0
        
        cmd_name = args[0]
        
        # Check for help on specific command
        if len(args) > 1 and (args[1] == "--help" or args[1] == "-h"):
            if cmd_name in self.commands:
                self._print_command_help(cmd_name)
                return 0
        
        if cmd_name not in self.commands:
            print(f"Error: No such command '{cmd_name}'.")
            return 2
        
        cmd_info = self.commands[cmd_name]
        cmd_args = args[1:]
        
        try:
            result = self._execute_function(cmd_info.func, cmd_args)
            return 0 if result is None else result
        except Exit as e:
            return e.code
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    
    def _execute_function(self, func: Callable, args: List[str]) -> Any:
        """Execute a function with parsed arguments."""
        sig = inspect.signature(func)
        params = sig.parameters
        
        # Parse function parameters
        param_infos = {}
        for param_name, param in params.items():
            if hasattr(param.default, '__class__') and isinstance(param.default, ParamInfo):
                param_infos[param_name] = param.default
            elif param.default != inspect.Parameter.empty:
                # Regular default value
                param_infos[param_name] = None
            else:
                # Required parameter (positional argument)
                param_infos[param_name] = None
        
        # Separate positional arguments and options
        positional_params = []
        option_params = {}
        
        for param_name, param in params.items():
            param_info = param_infos.get(param_name)
            if isinstance(param_info, ParamInfo):
                if param_info.is_argument:
                    positional_params.append((param_name, param_info, param))
                else:
                    option_params[param_name] = (param_info, param)
            else:
                # If no ParamInfo, treat as positional if no default, option otherwise
                if param.default == inspect.Parameter.empty:
                    positional_params.append((param_name, None, param))
                else:
                    option_params[param_name] = (None, param)
        
        # Parse arguments
        kwargs = {}
        positional_values = []
        i = 0
        
        while i < len(args):
            arg = args[i]
            
            if arg.startswith("--"):
                # Long option
                option_name = arg[2:]
                option_key = None
                
                # Find matching parameter
                for param_name, (param_info, param) in option_params.items():
                    if param_info and param_info.param_decls:
                        for decl in param_info.param_decls:
                            if decl.startswith("--") and decl[2:] == option_name:
                                option_key = param_name
                                break
                    elif param_name.replace("_", "-") == option_name:
                        option_key = param_name
                        break
                    if option_key:
                        break
                
                if option_key:
                    param_info, param = option_params[option_key]
                    # Check if it's a boolean flag
                    if param.annotation == bool or (param.default is not None and isinstance(param.default, bool)):
                        kwargs[option_key] = True
                        i += 1
                    else:
                        # Expect a value
                        if i + 1 < len(args):
                            value = args[i + 1]
                            # Type conversion
                            if param.annotation != inspect.Parameter.empty and param.annotation != str:
                                try:
                                    value = param.annotation(value)
                                except (ValueError, TypeError):
                                    pass
                            kwargs[option_key] = value
                            i += 2
                        else:
                            raise ValueError(f"Option --{option_name} requires a value")
                else:
                    raise ValueError(f"Unknown option: {arg}")
            else:
                # Positional argument
                positional_values.append(arg)
                i += 1
        
        # Assign positional values
        for idx, (param_name, param_info, param) in enumerate(positional_params):
            if idx < len(positional_values):
                value = positional_values[idx]
                # Type conversion
                if param.annotation != inspect.Parameter.empty and param.annotation != str:
                    try:
                        value = param.annotation(value)
                    except (ValueError, TypeError):
                        pass
                kwargs[param_name] = value
            elif param_info and param_info.default is not None:
                kwargs[param_name] = param_info.default
            elif param.default != inspect.Parameter.empty:
                kwargs[param_name] = param.default
            else:
                raise ValueError(f"Missing required argument: {param_name}")
        
        # Set defaults for options not provided
        for param_name, (param_info, param) in option_params.items():
            if param_name not in kwargs:
                if param_info and param_info.default is not None:
                    kwargs[param_name] = param_info.default
                elif param.default != inspect.Parameter.empty:
                    kwargs[param_name] = param.default
        
        return func(**kwargs)
    
    def _print_help(self):
        """Print help message."""
        print("Usage: [OPTIONS] COMMAND [ARGS]...")
        if self.help:
            print(f"\n{self.help}")
        
        if self.commands:
            print("\nCommands:")
            for cmd_name, cmd_info in sorted(self.commands.items()):
                help_text = cmd_info.help or ""
                if help_text:
                    help_text = help_text.strip().split('\n')[0]
                print(f"  {cmd_name:<20} {help_text}")
    
    def _print_command_help(self, cmd_name: str):
        """Print help for a specific command."""
        cmd_info = self.commands[cmd_name]
        print(f"Usage: {cmd_name} [OPTIONS] [ARGS]...")
        if cmd_info.help:
            print(f"\n{cmd_info.help}")


class CommandInfo:
    """Information about a registered command."""
    
    def __init__(self, func: Callable, name: str, help: Optional[str] = None):
        self.func = func
        self.name = name
        self.help = help