import argparse
import inspect
import sys
from typing import Any, Callable, Dict, List, Optional, Union, Type

from typer.params import Option, Argument

class Typer:
    """Main class to create CLI applications."""
    
    def __init__(
        self,
        name: Optional[str] = None,
        help: Optional[str] = None,
        no_args_is_help: bool = False,
    ):
        self.name = name
        self.help = help
        self.no_args_is_help = no_args_is_help
        self.commands: Dict[str, Dict[str, Any]] = {}
        self.callback_function = None
        self.parser = argparse.ArgumentParser(prog=name, description=help)
        self.subparsers = None
    
    def command(
        self,
        name: Optional[str] = None,
        help: Optional[str] = None,
    ) -> Callable:
        """Decorator to register a function as a command."""
        def decorator(f: Callable) -> Callable:
            cmd_name = name or f.__name__
            cmd_help = help or inspect.getdoc(f) or ""
            
            if self.subparsers is None:
                self.subparsers = self.parser.add_subparsers(dest="command", help="Commands")
            
            parser = self.subparsers.add_parser(cmd_name, help=cmd_help)
            signature = inspect.signature(f)
            
            for param_name, param in signature.parameters.items():
                param_type = param.annotation if param.annotation is not inspect.Parameter.empty else str
                default = param.default
                
                if isinstance(default, Option):
                    option_names = []
                    if default.name:
                        if isinstance(default.name, list):
                            option_names.extend(default.name)
                        else:
                            option_names.append(default.name)
                    else:
                        option_names.append(f"--{param_name}")
                    
                    if default.show_default and default.default is not ...:
                        help_text = f"{default.help or ''} (default: {default.default})"
                    else:
                        help_text = default.help
                    
                    parser.add_argument(
                        *option_names,
                        default=None if default.default is ... else default.default,
                        help=help_text,
                        required=default.required,
                        type=default.type if default.type is not None else param_type,
                    )
                elif isinstance(default, Argument):
                    parser.add_argument(
                        param_name,
                        default=None if default.default is ... else default.default,
                        help=default.help,
                        nargs="?" if default.default is not ... else None,
                        type=default.type if default.type is not None else param_type,
                    )
                elif param.default is not inspect.Parameter.empty:
                    parser.add_argument(
                        f"--{param_name}",
                        default=default,
                        help="",
                    )
                else:
                    parser.add_argument(
                        param_name,
                        help="",
                    )
            
            self.commands[cmd_name] = {
                "function": f,
                "parser": parser,
                "help": cmd_help,
            }
            return f
        
        return decorator
    
    def callback(self, **kwargs):
        """Decorator to register a function as the callback for the app."""
        def decorator(f: Callable) -> Callable:
            self.callback_function = f
            return f
        return decorator
    
    def __call__(self):
        """Run the application."""
        from typer import Exit
        
        # If no commands, add help command
        if not self.commands and not self.callback_function:
            self.parser.print_help()
            return 0
        
        args = self.parser.parse_args()
        cmd_name = getattr(args, "command", None)
        
        if not cmd_name and self.no_args_is_help:
            self.parser.print_help()
            return 0
        
        try:
            # If a command is specified
            if cmd_name and cmd_name in self.commands:
                cmd = self.commands[cmd_name]
                func = cmd["function"]
                
                # Extract the arguments for the function
                func_args = {}
                signature = inspect.signature(func)
                
                for param_name in signature.parameters:
                    if hasattr(args, param_name):
                        func_args[param_name] = getattr(args, param_name)
                
                result = func(**func_args)
                return 0 if result is None else result
            
            # If no command but we have a callback
            elif self.callback_function:
                # Extract the arguments for the callback
                func_args = {}
                signature = inspect.signature(self.callback_function)
                
                for param_name in signature.parameters:
                    if hasattr(args, param_name):
                        func_args[param_name] = getattr(args, param_name)
                
                result = self.callback_function(**func_args)
                return 0 if result is None else result
            
            # No command and no callback
            else:
                self.parser.print_help()
                return 0
                
        except Exit as e:
            return e.code