"""Main Typer application class."""

import sys
import inspect
from typing import Any, Callable, Dict, List, Optional, Tuple
from .models import Option, Argument
from .utils import Exit


class Typer:
    """Main application class for building CLI applications."""

    def __init__(
        self,
        name: Optional[str] = None,
        help: Optional[str] = None,
        invoke_without_command: bool = False,
    ):
        self.name = name
        self.help = help
        self.invoke_without_command = invoke_without_command
        self.commands: Dict[str, Callable] = {}
        self.command_help: Dict[str, Optional[str]] = {}

    def command(
        self,
        name: Optional[str] = None,
        help: Optional[str] = None,
    ) -> Callable:
        """Decorator to register a command."""
        def decorator(func: Callable) -> Callable:
            command_name = name or func.__name__
            self.commands[command_name] = func
            self.command_help[command_name] = help or func.__doc__
            return func
        return decorator

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Make the Typer instance callable."""
        return self.main(*args, **kwargs)

    def main(
        self,
        args: Optional[List[str]] = None,
        standalone_mode: bool = True,
    ) -> Any:
        """Main entry point for the CLI application."""
        if args is None:
            args = sys.argv[1:]

        try:
            return self._parse_and_run(args)
        except Exit as e:
            if standalone_mode:
                sys.exit(e.exit_code)
            else:
                raise
        except SystemExit as e:
            if standalone_mode:
                raise
            else:
                raise Exit(e.code if e.code is not None else 0)

    def _parse_and_run(self, args: List[str]) -> Any:
        """Parse arguments and run the appropriate command."""
        if not args:
            if self.commands:
                self._print_help()
                return None
            else:
                self._print_help()
                return None

        # Check for help flag
        if args[0] in ("--help", "-h"):
            self._print_help()
            return None

        # Check if first argument is a command
        if args[0] in self.commands:
            command_name = args[0]
            command_func = self.commands[command_name]
            command_args = args[1:]
            return self._run_command(command_func, command_args)
        else:
            # If we have commands but no matching command, show help
            if self.commands:
                self._print_help()
                raise Exit(2)
            else:
                # No commands defined, treat as single command
                return self._run_command(self._default_command, args)

    def _run_command(self, func: Callable, args: List[str]) -> Any:
        """Run a command with the given arguments."""
        sig = inspect.signature(func)
        params = sig.parameters

        # Parse arguments
        parsed_args = {}
        positional_args = []
        i = 0

        while i < len(args):
            arg = args[i]

            if arg in ("--help", "-h"):
                self._print_command_help(func)
                return None

            # Check if it's an option
            if arg.startswith("--"):
                option_name = arg[2:]
                if "=" in option_name:
                    key, value = option_name.split("=", 1)
                    parsed_args[key] = value
                    i += 1
                else:
                    if option_name in params:
                        if i + 1 < len(args) and not args[i + 1].startswith("--"):
                            parsed_args[option_name] = args[i + 1]
                            i += 2
                        else:
                            parsed_args[option_name] = True
                            i += 1
                    else:
                        i += 1
            elif arg.startswith("-") and len(arg) > 1 and arg[1] != "-":
                # Short option
                short_opt = arg[1]
                # Find matching parameter
                for param_name, param in params.items():
                    if hasattr(param.default, 'short_name') and param.default.short_name == short_opt:
                        if i + 1 < len(args) and not args[i + 1].startswith("-"):
                            parsed_args[param_name] = args[i + 1]
                            i += 2
                        else:
                            parsed_args[param_name] = True
                            i += 1
                        break
                else:
                    i += 1
            else:
                positional_args.append(arg)
                i += 1

        # Build final arguments
        final_args = {}
        positional_index = 0

        for param_name, param in params.items():
            if param_name in parsed_args:
                final_args[param_name] = parsed_args[param_name]
            elif positional_index < len(positional_args):
                final_args[param_name] = positional_args[positional_index]
                positional_index += 1
            elif param.default is not inspect.Parameter.empty:
                if isinstance(param.default, (Option, Argument)):
                    if param.default.default is not None:
                        final_args[param_name] = param.default.default
                else:
                    final_args[param_name] = param.default

        # Call the function
        result = func(**final_args)
        return result

    def _print_help(self) -> None:
        """Print help message."""
        if self.name:
            print(f"Usage: {self.name}")
        else:
            print("Usage: cli")

        if self.help:
            print(f"\n{self.help}")

        if self.commands:
            print("\nCommands:")
            for cmd_name in sorted(self.commands.keys()):
                cmd_help = self.command_help.get(cmd_name, "")
                if cmd_help:
                    print(f"  {cmd_name:<20} {cmd_help}")
                else:
                    print(f"  {cmd_name}")

    def _print_command_help(self, func: Callable) -> None:
        """Print help for a specific command."""
        sig = inspect.signature(func)
        params = sig.parameters

        print(f"Usage: {func.__name__}")

        if func.__doc__:
            print(f"\n{func.__doc__}")

        if params:
            print("\nOptions:")
            for param_name, param in params.items():
                param_help = ""
                if param.default is not inspect.Parameter.empty:
                    if isinstance(param.default, (Option, Argument)):
                        param_help = param.default.help or ""
                print(f"  --{param_name:<15} {param_help}")

    def _default_command(self, **kwargs: Any) -> Any:
        """Default command when no commands are registered."""
        return None