import sys
import inspect
import argparse
from .models import OptionInfo, ArgumentInfo, Exit
from .utils import echo

class Typer:
    def __init__(self, name=None, help=None, add_completion=True, no_args_is_help=False):
        self.name = name
        self.help = help
        self.commands = {}
        self.callback_func = None

    def command(self, name=None, help=None):
        def decorator(f):
            cmd_name = name or f.__name__.replace("_", "-")
            self.commands[cmd_name] = {
                "func": f,
                "help": help or inspect.getdoc(f)
            }
            return f
        return decorator

    def callback(self):
        def decorator(f):
            self.callback_func = f
            return f
        return decorator

    def __call__(self, args=None):
        if args is None:
            args = sys.argv[1:]
        
        parser = argparse.ArgumentParser(description=self.help, prog=self.name)
        
        if self.commands:
            subparsers = parser.add_subparsers(dest="_command_name", title="Commands")
            for name, cmd in self.commands.items():
                subparser = subparsers.add_parser(name, help=cmd["help"])
                _populate_parser(subparser, cmd["func"])
        elif self.callback_func:
            _populate_parser(parser, self.callback_func)
        
        try:
            parsed_args = parser.parse_args(args)
        except SystemExit as e:
            raise Exit(e.code)

        if hasattr(parsed_args, "_command_name") and parsed_args._command_name:
            cmd_name = parsed_args._command_name
            func = self.commands[cmd_name]["func"]
            kwargs = _extract_kwargs(parsed_args, func)
            try:
                func(**kwargs)
            except Exit as e:
                sys.exit(e.exit_code)
        elif self.callback_func and not self.commands:
            # Single command app via callback
            kwargs = _extract_kwargs(parsed_args, self.callback_func)
            try:
                self.callback_func(**kwargs)
            except Exit as e:
                sys.exit(e.exit_code)
        else:
            # If we have commands but none selected, argparse usually handles this if required=True on subparsers
            # but for compatibility, we print help if no command provided
            parser.print_help()
            raise Exit(0)

def run(func):
    parser = argparse.ArgumentParser(description=inspect.getdoc(func))
    _populate_parser(parser, func)
    
    try:
        parsed_args = parser.parse_args()
    except SystemExit as e:
        raise Exit(e.code)
        
    kwargs = _extract_kwargs(parsed_args, func)
    try:
        func(**kwargs)
    except Exit as e:
        sys.exit(e.exit_code)

def _populate_parser(parser, func):
    sig = inspect.signature(func)
    for name, param in sig.parameters.items():
        default = param.default
        annotation = param.annotation
        
        is_argument = False
        is_option = False
        param_info = None
        
        if isinstance(default, ArgumentInfo):
            is_argument = True
            param_info = default
            default_val = default.default
        elif isinstance(default, OptionInfo):
            is_option = True
            param_info = default
            default_val = default.default
        elif default == inspect.Parameter.empty:
            is_argument = True
            default_val = ...
        else:
            is_option = True
            default_val = default
            
        type_fn = None
        if annotation != inspect.Parameter.empty and annotation is not bool:
            type_fn = annotation
            
        help_text = None
        if param_info and param_info.kwargs.get("help"):
            help_text = param_info.kwargs.get("help")

        if is_argument:
            kwargs = {}
            if type_fn:
                kwargs["type"] = type_fn
            if help_text:
                kwargs["help"] = help_text
            
            if default_val != ...:
                kwargs["nargs"] = "?"
                kwargs["default"] = default_val
                
            parser.add_argument(name, **kwargs)
            
        elif is_option:
            flags = []
            if param_info and param_info.param_decls:
                flags = list(param_info.param_decls)
            else:
                flags = ["--" + name.replace("_", "-")]
            
            kwargs = {"dest": name}
            if help_text:
                kwargs["help"] = help_text

            if annotation is bool:
                if default_val is True:
                    kwargs["action"] = "store_false"
                else:
                    kwargs["action"] = "store_true"
            else:
                if type_fn:
                    kwargs["type"] = type_fn
                if default_val != ...:
                    kwargs["default"] = default_val
                else:
                    kwargs["required"] = True
            
            parser.add_argument(*flags, **kwargs)

def _extract_kwargs(parsed_args, func):
    sig = inspect.signature(func)
    kwargs = {}
    for name in sig.parameters:
        if hasattr(parsed_args, name):
            kwargs[name] = getattr(parsed_args, name)
    return kwargs