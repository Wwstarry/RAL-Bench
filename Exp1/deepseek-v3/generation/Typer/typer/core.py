import inspect
import sys
from typing import Any, Callable, Dict, List, Optional, Union

from .models import ArgumentInfo, OptionInfo
from .main import echo, Exit


class Typer:
    def __init__(
        self,
        name: Optional[str] = None,
        help: Optional[str] = None,
        add_completion: bool = True,
    ):
        self.name = name or sys.argv[0] if sys.argv else "typer"
        self.help = help
        self.add_completion = add_completion
        self._commands: Dict[str, Callable] = {}
        self._default_command: Optional[str] = None

    def command(
        self,
        name: Optional[str] = None,
        help: Optional[str] = None,
    ) -> Callable:
        def decorator(func: Callable) -> Callable:
            command_name = name or func.__name__
            self._commands[command_name] = func
            if hasattr(func, "_typer_default_command"):
                self._default_command = command_name
            return func
        return decorator

    def callback(self, func: Callable) -> Callable:
        # For now, treat callback same as command
        return self.command()(func)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.run(*args, **kwargs)

    def run(self, args: Optional[List[str]] = None) -> Any:
        if args is None:
            args = sys.argv[1:]

        if not args and self._default_command:
            command_name = self._default_command
            command_args = []
        elif not args:
            self._print_help()
            raise Exit(0)
        else:
            command_name = args[0]
            command_args = args[1:]

        if command_name in ["--help", "-h"]:
            self._print_help()
            raise Exit(0)

        if command_name not in self._commands:
            echo(f"Error: No such command '{command_name}'", err=True)
            self._print_help()
            raise Exit(2)

        command_func = self._commands[command_name]
        return self._invoke_command(command_func, command_args)

    def _invoke_command(self, func: Callable, args: List[str]) -> Any:
        try:
            parsed_args = self._parse_args(func, args)
            result = func(**parsed_args)
            if result is not None and isinstance(result, int):
                raise Exit(result)
            return result
        except Exit as e:
            raise e
        except Exception as e:
            echo(f"Error: {e}", err=True)
            raise Exit(1)

    def _parse_args(self, func: Callable, args: List[str]) -> Dict[str, Any]:
        signature = inspect.signature(func)
        parameters = list(signature.parameters.values())
        
        parsed_args = {}
        arg_index = 0
        i = 0
        
        while i < len(args):
            arg = args[i]
            
            if arg.startswith("--"):
                # Long option
                if "=" in arg:
                    name, value = arg[2:].split("=", 1)
                else:
                    name = arg[2:]
                    if i + 1 < len(args) and not args[i + 1].startswith("-"):
                        value = args[i + 1]
                        i += 1
                    else:
                        value = True
                parsed_args[name.replace("-", "_")] = self._convert_value(value)
            elif arg.startswith("-"):
                # Short option
                name = arg[1:]
                if i + 1 < len(args) and not args[i + 1].startswith("-"):
                    value = args[i + 1]
                    i += 1
                else:
                    value = True
                parsed_args[name] = self._convert_value(value)
            else:
                # Positional argument
                if arg_index < len(parameters):
                    param = parameters[arg_index]
                    parsed_args[param.name] = self._convert_value(arg)
                    arg_index += 1
                else:
                    # Extra argument - treat as error for now
                    raise ValueError(f"Unexpected argument: {arg}")
            
            i += 1
        
        # Fill in missing parameters with defaults
        for param in parameters:
            if param.name not in parsed_args:
                if param.default is not param.empty:
                    parsed_args[param.name] = param.default
                else:
                    raise ValueError(f"Missing required parameter: {param.name}")
        
        return parsed_args

    def _convert_value(self, value: Any) -> Any:
        if value is True:
            return True
        elif isinstance(value, str):
            if value.lower() == "true":
                return True
            elif value.lower() == "false":
                return False
            try:
                return int(value)
            except ValueError:
                try:
                    return float(value)
                except ValueError:
                    return value
        return value

    def _print_help(self):
        echo(f"Usage: {self.name} [OPTIONS] COMMAND [ARGS]...")
        echo()
        if self.help:
            echo(self.help)
            echo()
        echo("Commands:")
        for cmd_name in sorted(self._commands.keys()):
            cmd_func = self._commands[cmd_name]
            help_text = getattr(cmd_func, "_typer_help", "") or cmd_func.__doc__ or ""
            echo(f"  {cmd_name:<15} {help_text}")
        echo()
        echo("Options:")
        echo("  --help, -h        Show this message and exit.")


def default(func: Callable) -> Callable:
    func._typer_default_command = True
    return func