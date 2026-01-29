"""
Core Typer implementation.
"""
import sys
import inspect
import argparse
from typing import Any, Callable, Dict, List, Optional, Union, get_type_hints
from dataclasses import dataclass, field
from enum import Enum


class Exit(Exception):
    """Exception to exit the program with a status code."""
    def __init__(self, code: int = 0):
        self.code = code
        super().__init__(f"Exit with code {code}")


def echo(message: str = "", **kwargs: Any) -> None:
    """Print message to stdout."""
    print(message, **kwargs)


@dataclass
class ParameterConfig:
    """Configuration for a command parameter."""
    default: Any = None
    help: Optional[str] = None
    show_default: bool = False
    hidden: bool = False
    # For Option
    param_decls: Optional[List[str]] = None
    # For Argument
    positional: bool = False


class Option:
    """Declare a CLI option."""
    def __init__(
        self,
        default: Any = ...,
        *param_decls: str,
        help: Optional[str] = None,
        show_default: bool = False,
        hidden: bool = False,
    ):
        self.config = ParameterConfig(
            default=default,
            help=help,
            show_default=show_default,
            hidden=hidden,
            param_decls=list(param_decls) if param_decls else None,
        )


class Argument:
    """Declare a CLI argument."""
    def __init__(
        self,
        default: Any = ...,
        help: Optional[str] = None,
        show_default: bool = False,
        hidden: bool = False,
    ):
        self.config = ParameterConfig(
            default=default,
            help=help,
            show_default=show_default,
            hidden=hidden,
            positional=True,
        )


class Typer:
    """Typer application."""
    def __init__(
        self,
        name: Optional[str] = None,
        help: Optional[str] = None,
        add_completion: bool = False,
    ):
        self.name = name
        self.help = help
        self._commands: Dict[str, Callable] = {}
        self._default_command: Optional[str] = None

    def command(
        self,
        name: Optional[str] = None,
        help: Optional[str] = None,
        hidden: bool = False,
    ) -> Callable:
        """Decorator to add a command."""
        def decorator(func: Callable) -> Callable:
            cmd_name = name or func.__name__
            self._commands[cmd_name] = func
            if self._default_command is None:
                self._default_command = cmd_name
            return func
        return decorator

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Run the CLI application."""
        return self.run(*args, **kwargs)

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run the CLI application."""
        if not args:
            args = sys.argv[1:]
        
        parser = self._create_parser()
        
        if not self._commands:
            # No commands, just run the function directly if it's a single function app
            return
        
        # Parse args to get command name
        parsed_args, remaining = parser.parse_known_args(args)
        
        if not hasattr(parsed_args, 'command') or parsed_args.command is None:
            # No command specified, show help
            parser.print_help()
            raise Exit(0)
        
        command_name = parsed_args.command
        if command_name not in self._commands:
            print(f"Error: Unknown command '{command_name}'")
            parser.print_help()
            raise Exit(2)
        
        command_func = self._commands[command_name]
        
        # Parse command-specific arguments
        cmd_parser = self._create_command_parser(command_name, command_func)
        try:
            cmd_args = cmd_parser.parse_args(remaining)
        except SystemExit:
            # argparse printed help or error, exit appropriately
            raise Exit(2)
        
        # Prepare arguments for the command function
        func_args = {}
        sig = inspect.signature(command_func)
        type_hints = get_type_hints(command_func)
        
        for param_name in sig.parameters:
            if hasattr(cmd_args, param_name):
                value = getattr(cmd_args, param_name)
                # Convert Enum if needed
                if param_name in type_hints:
                    type_hint = type_hints[param_name]
                    if isinstance(type_hint, type) and issubclass(type_hint, Enum):
                        if isinstance(value, str):
                            value = type_hint[value]
                func_args[param_name] = value
        
        try:
            result = command_func(**func_args)
            if isinstance(result, int):
                raise Exit(result)
            return result
        except Exit as e:
            raise e
        except Exception as e:
            print(f"Error: {e}")
            raise Exit(1)

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser."""
        parser = argparse.ArgumentParser(
            prog=self.name,
            description=self.help,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        
        if self._commands:
            subparsers = parser.add_subparsers(
                dest='command',
                title='commands',
                help='Available commands',
                metavar='COMMAND'
            )
            
            for cmd_name, cmd_func in self._commands.items():
                cmd_help = cmd_func.__doc__ or ""
                subparser = subparsers.add_parser(
                    cmd_name,
                    help=cmd_help.split('\n')[0] if cmd_help else None,
                    description=cmd_help,
                    formatter_class=argparse.RawDescriptionHelpFormatter,
                )
        
        return parser

    def _create_command_parser(self, command_name: str, command_func: Callable) -> argparse.ArgumentParser:
        """Create parser for a specific command."""
        cmd_help = command_func.__doc__ or ""
        parser = argparse.ArgumentParser(
            prog=f"{self.name or 'typer'} {command_name}",
            description=cmd_help,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            add_help=False,
        )
        
        sig = inspect.signature(command_func)
        type_hints = get_type_hints(command_func)
        defaults = {}
        
        # Get defaults from function signature
        for param_name, param in sig.parameters.items():
            if param.default is not inspect.Parameter.empty:
                defaults[param_name] = param.default
        
        # Process parameters
        for param_name, param in sig.parameters.items():
            # Check if this is an Option or Argument
            annotation = param.annotation
            
            # Get default from annotation if it's an Option/Argument
            config = None
            if isinstance(annotation, (Option, Argument)):
                config = annotation.config
                # Update defaults from config
                if config.default is not ...:
                    defaults[param_name] = config.default
            
            # Determine if this is an option or argument
            is_option = True
            if isinstance(annotation, Argument):
                is_option = False
            elif config and config.positional:
                is_option = False
            elif param_name in defaults and param_name != 'self':
                # Parameters with defaults are options
                is_option = True
            else:
                # Try to infer from type hint
                type_hint = type_hints.get(param_name)
                if type_hint and isinstance(type_hint, type) and issubclass(type_hint, bool):
                    is_option = True
                else:
                    # Positional arguments come before options with defaults
                    is_option = param_name in defaults
            
            if is_option:
                # Add as option
                option_names = []
                if config and config.param_decls:
                    option_names = config.param_decls
                else:
                    # Generate option name
                    option_name = f"--{param_name.replace('_', '-')}"
                    option_names = [option_name]
                
                # Get default value
                default_val = defaults.get(param_name, ...)
                if default_val is ...:
                    default_val = None
                
                # Determine type and action
                type_hint = type_hints.get(param_name)
                action = 'store'
                nargs = None
                const = None
                
                if type_hint == bool:
                    if default_val is True:
                        action = 'store_false'
                        # For store_false, we need to invert the default
                        default_val = False
                    else:
                        action = 'store_true'
                        default_val = False
                elif type_hint and isinstance(type_hint, type) and issubclass(type_hint, Enum):
                    # Use choices for Enum
                    parser.add_argument(
                        *option_names,
                        choices=[e.name for e in type_hint],
                        default=default_val,
                        help=config.help if config else None,
                        required=default_val is None,
                    )
                    continue
                elif default_val is None and type_hint is not None:
                    # Optional type
                    pass
                
                parser.add_argument(
                    *option_names,
                    action=action,
                    default=default_val,
                    help=config.help if config else None,
                    required=default_val is None and action == 'store',
                    nargs=nargs,
                    const=const,
                )
            else:
                # Add as positional argument
                parser.add_argument(
                    param_name,
                    help=config.help if config else None,
                    default=defaults.get(param_name),
                )
        
        return parser